#!/usr/bin/env python

from __future__ import annotations

import asyncio
import json
from typing import Callable

from pydantic import parse_obj_as

from metagpt.actions import Action
from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.tools.search_engine import SearchEngine
from metagpt.tools.web_browser_engine import WebBrowserEngine, WebBrowserEngineType
from metagpt.utils.common import OutputParser
from metagpt.utils.text import generate_prompt_chunk


LANG_PROMPT = "please act as {language} people, you consider their culture in your output. must respond in {language}"

RESEARCH_BASE_SYSTEM = """You are an AI critical thinker research assistant. Your sole purpose is to write well \
written, critically acclaimed, objective and structured reports on the given text."""

RESEARCH_TOPIC_SYSTEM = "You are an AI researcher assistant, and your research topic is:\n{topic}\n"


SEARCH_TOPIC_PROMPT = """Please provide just upto {keyword_num} important keyword related to your research topic for Google search. \
You should imagine like human and make a keyword like human. find most nice keyword that is most efficient to find ideal result.
Your response must be in JSON format, for example: ["keyword1",...].
### Requirements : 

1. Remember you should give upto {keyword_num} keyword
"""

# SUMMARIZE_SEARCH_PROMPT = """
# ### Requirements

# 1. The keywords related to your research topic and the search results are shown in the "Search Result Information" section.
# 2. Provide up to {decomposition_nums} queries related to your research topic base on the search results.
# 3. Please respond in the following JSON format: ["query1", "query2", "query3", ...].
# 4. you don't have to respond in english. show me result mix of korean version and english version.
# 5. It's a good idea to pick keywords that are meaningful in order to *gather as much information as possible* to achieve your topic.

# ### Search Result Information
# {search_results}
# """

COLLECT_AND_RANKURLS_PROMPT = """
Your role is ranking every url based on relevancy between query and result snippet
### Query
{query}

### The online search results
{results}

### Requirements
- rank results' indices in JSON format, like [0, 1, 3, 2, ...], without including other words.
- No explanation needed. Only give me result list. like your output only inlcude like [0,1,2,3,...]
"""

WEB_BROWSE_AND_SUMMARIZE_PROMPT = """
Utilize the text in the "Reference Information" section to respond to the question "{query}".

### Reference Information
{content}

### Requirments
1. If the question cannot be directly answered using the text, but the text is related to the research topic, please provide \
a comprehensive summary of the text.
2. If the text is entirely unrelated to the research topic, please reply with a simple text "Not relevant."
4. Include all relevant factual information, numbers, statistics, etc., if available.
5. If you can't access, tplease reply with "I can't access link" without any explanation.
6. Never make it up, if you cannot access, Never give me information. 

"""


CONDUCT_RESEARCH_PROMPT = """
### Reference Information
{content}

### Requirements
Please provide a detailed research report in response to the following topic: "{topic}", using the information provided \
above. The report must meet the following requirements:

- Focus on directly addressing the chosen topic.
- Ensure a well-structured and in-depth presentation, incorporating relevant facts and figures where available.
- Present data and findings in an intuitive manner, utilizing feature comparative tables, if applicable.
- formatted with Markdown syntax following APA style guidelines.
- Include all source URLs in APA format at the end of the report.
- Make sure to include the essential information in each URL to create a natural logical flow.  


### Most Important
- *Make sure to include the link you referenced in, and Put all the links you refer to in the reference part.*
- *Never make it up. Never Make a User review or something, Write everything based on reference information*
- Remember : **For each sentence, indicate which url you referenced. if the sentence come from link 1, then you should write like sentence[1]**

"""

SUMMARY_REPORT_PROMPT = """
Summarize the Markdown text into a single paragraph,

---- Report ------------
{report}
---- Requirments -------
- Output is Markdown text
- Paragraph must not exceed 300 words
- Show references with hyperlinks respectively APA form.
- You must include Reference link you used.
"""


class GetQueries(Action):
    """Action class to collect links from a search engine."""

    # 얘는 기본적으로 GPT4 이용
    def __init__(
        self,
        name: str = "",
        *args,
        rank_func: Callable[[list[str]], None] | None = None,
        **kwargs,
    ):
        super().__init__(name, *args, **kwargs)
        self.desc = "Make Proper Query from problem."
        self.search_engine = SearchEngine()
        self.rank_func = rank_func
        if CONFIG.model_for_researcher_keyword:
            self.llm.model = CONFIG.model_for_researcher_keyword
        logger.log("DEVELOP", "keyword llm model is " + self.llm.model)

    async def run(
        self,
        topic: str,
        keyword_num: int = 4,
        system_text: str = RESEARCH_BASE_SYSTEM,
    ) -> dict[str, list[str]]:
        """Run the action to collect links.

        Args:
            topic: The research topic.
            keyword_num: The number of search query to generate.
            url_per_query: The number of URLs to collect per search question.
            system_text: The system text.

        Returns:
            A dictionary containing the search questions as keys and the collected URLs as values.
        """
        system_text = system_text if system_text else RESEARCH_TOPIC_SYSTEM.format(topic=topic)
        search_topic_prompt = SEARCH_TOPIC_PROMPT.format(keyword_num=keyword_num)
        queries = await self._aask(search_topic_prompt, [system_text])
        logger.log("DEVELOP", queries)
        try:
            queries = OutputParser.extract_struct(queries, list)
            queries = parse_obj_as(list[str], queries)
        except Exception as e:
            logger.exception(
                f'fail to get keywords related to the research topic "{topic}" for {e}'
            )
            queries = [topic]

        return queries


class RankLinks(Action):
    """Action class to collect links from a search engine."""

    # 얘는 기본적으로 GPT4 이용
    def __init__(
        self,
        name: str = "",
        *args,
        rank_func: Callable[[list[str]], None] | None = None,
        **kwargs,
    ):
        super().__init__(name, *args, **kwargs)
        self.desc = "Do Query and get links and rank it."
        self.search_engine = SearchEngine()
        self.rank_func = rank_func
        if CONFIG.model_for_researcher_rank:
            self.llm.model = CONFIG.model_for_researcher_rank
        logger.log("DEVELOP", "rank llm model is " + self.llm.model)

    async def run(
        self,
        topic: str,
        queries: list,
        url_per_query: int = 4,
    ) -> dict[str, list[str]]:
        """Run the action to rank links.

        Args:
            topic: The research topic.
            queries: Want to Query and Rank result links
            url_per_query: The number of URLs to collect per search question. Search 3 times bigger space

        Returns:
            A dictionary containing the search questions as keys and the collected URLs as values.
        """
        ret = {}
        tasks = []
        for query in queries:
            task = self._search_and_rank_urls(topic, query, url_per_query)
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        for i, query in enumerate(queries):
            ret[query] = results[i]
        return ret

    async def _search_and_rank_urls(
        self, topic: str, query: str, num_results: int = 4
    ) -> list[str]:
        """Search and rank URLs based on a query.

        Args:
            topic: The research topic.
            query: The search query.
            num_results: The number of URLs to collect. - 1

        Returns:
            A list of ranked URLs.
        """
        max_results = max(num_results * 3, 6)
        results = await self.search_engine.run(query, max_results=max_results, as_string=False)
        _results = "\n".join(f"{i}: {j}" for i, j in zip(range(max_results), results))
        prompt = COLLECT_AND_RANKURLS_PROMPT.format(topic=topic, query=query, results=_results)
        logger.debug(prompt)
        indices = await self._aask(prompt)

        try:
            indices = OutputParser.extract_struct(indices, list)
            assert all(isinstance(i, int) for i in indices)
        except Exception as e:
            logger.exception(f"fail to rank results for {e}")
            indices = list(range(max_results))
        results = [results[i] for i in indices]
        if self.rank_func:
            results = self.rank_func(results)
        return [i["link"] for i in results[:num_results]]


class WebBrowseAndSummarize(Action):
    """Action class to explore the web and provide summaries of articles and webpages."""

    def __init__(
        self,
        *args,
        browse_func: Callable[[list[str]], None] | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if CONFIG.model_for_researcher_summary:
            self.llm.model = CONFIG.model_for_researcher_summary
        self.web_browser_engine = WebBrowserEngine(
            engine=WebBrowserEngineType.CUSTOM if browse_func else None,
            run_func=browse_func,
        )
        self.desc = "Explore the web and provide summaries of articles and webpages."

    async def run(
        self,
        url: str,
        *urls: str,
        query: str,
        system_text: str = RESEARCH_BASE_SYSTEM,
    ) -> dict[str, str]:
        """Run the action to browse the web and provide summaries.

        Args:
            url: The main URL to browse.
            urls: Additional URLs to browse.
            query: The research question.
            system_text: The system text.

        Returns:
            A dictionary containing the URLs as keys and their summaries as values.
        """
        contents = await self.web_browser_engine.run(url, *urls)
        if not urls:
            contents = [contents]

        summaries = {}
        prompt_template = WEB_BROWSE_AND_SUMMARIZE_PROMPT.format(query=query, content="{}")

        async def process_content(url, content):
            content = content.inner_text
            chunk_summaries = []
            for prompt in generate_prompt_chunk(
                content, prompt_template, self.llm.model, system_text, CONFIG.max_tokens_rsp
            ):
                logger.debug(prompt)
                summary = await self._aask(prompt, [system_text])
                if summary == "Not relevant.":
                    continue
                chunk_summaries.append(summary)

            if not chunk_summaries:
                summaries[url] = None
                return

            if len(chunk_summaries) == 1:
                summaries[url] = chunk_summaries[0]
                return

            content = "\n".join(chunk_summaries)
            prompt = WEB_BROWSE_AND_SUMMARIZE_PROMPT.format(query=query, content=content)
            summary = await self._aask(prompt, [system_text])
            summaries[url] = summary

        tasks = []
        for u, content in zip([url, *urls], contents):
            tasks.append(process_content(u, content))
        await asyncio.gather(*tasks)
        return summaries


class ConductResearch(Action):
    """Action class to conduct research and generate a research report."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if CONFIG.model_for_researcher_report:
            self.llm.model = CONFIG.model_for_researcher_report

    async def run(
        self,
        topic: str,
        content: str,
        system_text: str = RESEARCH_BASE_SYSTEM,
    ) -> str:
        """Run the action to conduct research and generate a research report.

        Args:
            topic: The research topic.
            content: The content for research.
            system_text: The system text.

        Returns:
            The generated research report.
        """
        prompt = CONDUCT_RESEARCH_PROMPT.format(topic=topic, content=content)
        logger.debug(prompt)
        self.llm.auto_max_tokens = True
        await asyncio.sleep(0.5)  # For safe writing
        return await self._aask(prompt, [system_text])


class ReportSummary(Action):
    """Do Summary for"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if CONFIG.model_for_report_summary:
            self.llm.model = CONFIG.model_for_report_summary

    async def run(
        self,
        report: str,
        system_text: str = RESEARCH_BASE_SYSTEM,
    ) -> str:
        """Run the action to conduct research and generate a research report.

        Args:
            topic: The research topic.
            content: The content for research.
            system_text: The system text.

        Returns:
            The generated research report.
        """
        prompt = SUMMARY_REPORT_PROMPT.format(report=report)
        logger.debug(prompt)
        self.llm.auto_max_tokens = True
        await asyncio.sleep(0.5)  # For safe writing
        return await self._aask(prompt, [system_text])


def get_research_system_text(topic: str, language: str):
    """Get the system text for conducting research.

    Args:
        topic: The research topic.
        language: The language for the system text.

    Returns:
        The system text for conducting research.
    """
    return " ".join(
        (RESEARCH_TOPIC_SYSTEM.format(topic=topic), LANG_PROMPT.format(language=language))
    )


_example_report = """
# Research Report: ILM Powered Multi-Agent Systems and AGI

## Introduction
In recent years, there has been growing interest in the development of Artificial General Intelligence (AGI) systems, which possess the ability to perform any intellectual task that a human being can do. One approach to enhancing the capabilities of AGI systems is through the use of Influence Learning Mechanism (ILM) powered multi-agent systems. This research report aims to explore the concept of ILM powered multi-agent systems and their application in AGI. The report will provide an overview of multi-agent systems, discuss the integration of ILM in AGI, and explore the potential benefits and challenges associated with this approach.

## Multi-Agent Systems
Multi-agent systems are computerized systems composed of multiple interacting intelligent agents. These systems are capable of solving complex problems that are difficult or impossible for individual agents or monolithic systems to solve. The intelligence of these agents can be based on various approaches, including methodic, functional, procedural approaches, algorithmic search, or reinforcement learning [^1] [^2]. Multi-agent systems can consist of software agents, robots, humans, or human teams, and the agents can be categorized into passive agents (without goals), active agents with simple goals, and cognitive agents capable of complex calculations [^1] [^2]. The agent environments can be virtual, discrete, or continuous [^1] [^2].

## ILM in AGI
ILM, or Influence Learning Mechanism, is a concept that can be integrated into AGI systems to enhance their learning and adaptation capabilities. The NARS (Non-Axiomatic Reasoning System) framework is an example of an AGI system that incorporates ILM [^13]. In the NARS framework, the control mechanism of the system is not entirely designed by the system's creator but is adjusted and fine-tuned by the system itself based on its experience [^13]. The system's resource allocation and task prioritization are influenced by its emotions and desires, which are appraised based on the system's experience and feedback [^13]. This adaptive behavior allows the system to respond to changing circumstances and achieve its goals efficiently [^13].

The NARS framework also incorporates self-organization, where the system's behavior is not predetermined but is influenced by its experience and feedback [^13]. This self-organization enables the system to adapt to its environment, learn from experience, and achieve its goals effectively [^13]. The NARS framework allows the system to organize its atomic operations into compound operations, avoiding repeated planning or searching [^13]. This recursive self-improvement model aligns with the concept of ILM in AGI [^13].

## Benefits and Challenges
The integration of ILM in AGI systems offers several potential benefits. By incorporating ILM, AGI systems can enhance their learning and adaptation capabilities, allowing them to respond to changing circumstances and achieve goals more efficiently [^13]. The self-organization aspect of ILM enables AGI systems to adapt to their environment and learn from experience, leading to improved performance and problem-solving abilities [^13]. Additionally, the recursive self-improvement model of ILM can contribute to the development of more sophisticated AGI systems [^13].

However, there are also challenges associated with the integration of ILM in AGI systems. One challenge is the design and implementation of the ILM mechanism itself, as it requires careful consideration of factors such as resource allocation, task prioritization, and emotional appraisal [^13]. Another challenge is the potential for unintended consequences or biases in the learning and adaptation process, which may require additional safeguards and oversight [^13]. Furthermore, the development of AGI systems with ILM requires significant computational resources and expertise, which may pose practical challenges [^13].

## Conclusion
ILM powered multi-agent systems offer a promising approach to enhancing the capabilities of AGI systems. By integrating ILM, AGI systems can improve their learning and adaptation abilities, leading to more efficient problem-solving and performance. The self-organization aspect of ILM enables AGI systems to adapt to their environment and learn from experience, further enhancing their capabilities. However, the integration of ILM in AGI systems also presents challenges, such as the design and implementation of the ILM mechanism and the potential for unintended consequences or biases. Further research and development are needed to overcome these challenges and fully realize the potential of ILM powered multi-agent systems in AGI.

## References
[^1]: Wikipedia. (n.d.). Multi-agent system. Retrieved from [https://en.wikipedia.org/wiki/Multi-agent_system](https://en.wikipedia.org/wiki/Multi-agent_system)
[^2]: Wooldridge, M. (2009). An Introduction to MultiAgent Systems. John Wiley & Sons.
[^13]: NARS Research Group. (n.d.). Influence Learning Mechanism. Retrieved from [https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7805877/](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7805877/)
"""

__example_websummaies = """
url: https://arxiv.org/abs/2303.12712
summary: I apologize, but I am unable to access the reference information you provided. Could you please provide alternative reference information or specify any particular aspects of AGI that you would like me to focus on?
---
url: https://www.reddit.com/r/learnmachinelearning/comments/a4gmet/what_are_some_good_papers_on_artificial_general/
summary: Based on the provided text, here is a summary of the relevant information:

- The original question asked for good papers on Artificial General Intelligence (AGI).
- Some users in the discussion mentioned that AGI does not currently exist and that there are no full-fledged implementations of AGI in the wild.
- One user shared a link to a paper titled "ALGORITHMIC THEORIES OF EVERYTHING" by the creator of the LSTM Net. The link provided is https://arxiv.org/pdf/quant-ph/0011122.pdf.
- Another user suggested looking into Schmidhuber's work on SeedAI, which is considered the closest thing to AGI, although it is practically useless.
- One user mentioned OpenCOG as an approach to AGI architecture, but noted that there isn't a full-fledged implementation of AGI yet.

Based on this information, it seems that there is limited research and implementation of AGI currently available. The provided link to the paper "ALGORITHMIC THEORIES OF EVERYTHING" may provide some insights into AGI. However, it is important to note that AGI is still a developing field, and further research is needed to fully understand its elements and possibilities.
---
url: https://www.researchgate.net/publication/271390398_Artificial_General_Intelligence_Concept_State_of_the_Art_and_Future_Prospects
summary: Based on the information provided, here is a summary of the relevant text:

- The initial question asked for good papers on Artificial General Intelligence (AGI). Some responses suggested that AGI does not currently exist and that the concept of "general intelligence" is contrived.
- One user shared a link to a paper titled "ALGORITHMIC THEORIES OF EVERYTHING" on arXiv (https://arxiv.org/pdf/quant-ph/0011122.pdf). The paper discusses the creator of the LSTM Net and their work on algorithmic theories of everything.
- Another user mentioned Schmidhuber's work on SeedAI as the closest thing to AGI, but noted that it is practically useless.
- OpenCOG was mentioned as one approach to an AGI architecture, but it was noted that there isn't a full-fledged implementation of AGI in the wild.

Based on this information, it seems that there is limited research or papers specifically focused on AGI. The concept of AGI is still a topic of debate and there is no consensus on its definition or existence. The mentioned papers and approaches provide some insights into related areas, such as algorithmic theories and AGI architectures, but they do not represent comprehensive research on AGI itself.
---
url: https://www.frontiersin.org/articles/10.3389/frai.2023.1226990
summary: $${{{{{{{\mathcal{L}}}}}}}}_{gen} = \cos({{{{{{{\bf{z}}}}}}}}}^{(i)}, {{{{{{{\bf{z}}}}}}}}}^{(t)}).$$

With the resultant gradients, we update the input code collection U by back-propagation. After repeating the updating step with multiple iterations, we finally obtain a code collection U that can be regarded as BriVL's response/imagination about the input text. To generate a photo-realistic image, we feed the updated code collection U into the generator g and obtain the final generated image x(i). The algorithm for text-to-image generation is summarized in Algorithm 2.

Algorithm 2

Text-to-Image Generation

Input: The pre-trained image and text encoder f(i) and f(t) of our BriVL

   The pre-trained VQGAN generator g

   A piece of text x(t)

   A randomly initialized code collection U

   A learning rate parameter λ

Output: The updated code collection U

1: Obtain the text embedding z(t) = f(t)(x(t));

2: for all iteration = 1, 2, ⋯  , MaxIteration do

3:    Obtain the image embedding z(i) = f(i)(g(U));

4:    Compute Lgen with Eq. (14);

5:    Compute the gradients \({\nabla }_{{U}}{{{{{{\mathcal{L}}}}}}}}_{gen}\);

6:    Update U using gradient descent with λ;

7: end for

8: return the updated code collection U.

Formalization of zero-shot remote sensing scene classification

Zero-shot remote sensing scene classification is a task to classify remote sensing images into predefined classes without any training samples from these classes. Given a set of unseen classes \({{{{{{{\mathcal{C}}}}}}}}_{u}\) and a set of seen classes \({{{{{{{\mathcal{C}}}}}}}}_{s}\), the goal is to learn a classifier that can generalize well to the unseen classes. Formally, let \({{{{{{{\mathcal{D}}}}}}}}_{s}\) and \({{{{{{{\mathcal{D}}}}}}}}_{u}\) be the training set and test set, respectively, where \({{{{{{{\mathcal{D}}}}}}}}_{s}\) contains samples from the seen classes and \({{{{{{{\mathcal{D}}}}}}}}_{u}\) contains samples from the unseen classes. The task is to learn a classifier f that maps an input sample x to its corresponding class label y, where y ∈ \({{{{{{{\mathcal{C}}}}}}}}_{s}\) for \({{{{{{{\mathcal{D}}}}}}}}_{s}\) and y ∈ \({{{{{{{\mathcal{C}}}}}}}}_{u}\) for \({{{{{{{\mathcal{D}}}}}}}}_{u}\). The classifier f is trained on \({{{{{{{\mathcal{D}}}}}}}}_{s}\) and evaluated on \({{{{{{{\mathcal{D}}}}}}}}_{u}\). The performance is measured by the classification accuracy.
---
url: https://www.nature.com/articles/s41467-022-30761-2
summary: $${{{{{{{\mathcal{L}}}}}}}}_{gen} = \cos\left({{{{{{{\bf{z}}}}}}}}}^{(i)}, {{{{{{{\bf{z}}}}}}}}}^{(t)}\right).$$

With the resultant gradients, we update the input code collection U by back-propagation. After repeating the updating step with multiple iterations, we finally obtain a code collection U, which can be regarded as the latent representation of the generated image conditioned on the input text. The latent representation U is then fed into the generator g to obtain the final generated image. The algorithm for text-to-image generation is summarized in Algorithm 2.

Algorithm 2

Text-to-Image Generation

Input: The pre-trained image and text encoder f(i) and f(t) of our BriVL

   The pre-trained VQGAN generator g

   A piece of text x(t)

   A randomly initialized code collection U

   A learning rate parameter λ

Output: The updated code collection U

1: Obtain the text embedding z(t) = f(t)(x(t));

2: for all iteration = 1, 2, ⋯  , MaxIteration do

3:    Obtain the image x(i) = g(U);

4:    Obtain the image embedding z(i) = f(i)(x(i));

5:    Compute Lgen with Eq. (14);

6:    Compute the gradients \({\nabla }_{{U}}{{{{{{{\mathcal{L}}}}}}}}_{gen}\);

7:    Update U using gradient descent with λ;

8: end for

9: return the updated code collection U.

Formalization of zero-shot remote sensing scene classification

Zero-shot remote sensing scene classification is a task to classify remote sensing images into predefined semantic categories without any training samples from the target categories. Given a dataset \({{{{{{{\mathcal{D}}}}}}}}=\{({x}_{i},{y}_{i})| i=1,\cdots ,N\}\), where \({x}_{i}\) is the i-th remote sensing image and \({y}_{i}\) is its corresponding label, we split the dataset into two subsets: seen classes \({{{{{{{\mathcal{D}}}}}}}}_{s}\) and unseen classes \({{{{{{{\mathcal{D}}}}}}}}_{u}\). The goal is to train a classifier on \({{{{{{{\mathcal{D}}}}}}}}_{s}\) and evaluate its performance on \({{{{{{{\mathcal{D}}}}}}}}_{u}\). For each image \({x}_{i}\) in \({{{{{{{\mathcal{D}}}}}}}}_{u}\), we obtain its image embedding \({{{{{{{\bf{z}}}}}}}}_{i}^{(i)}\) by forwarding it through the image encoder f(i). Similarly, for each class label \({y}_{j}\) in \({{{{{{{\mathcal{D}}}}}}}}_{s}\), we obtain its class embedding \({{{{{{{\bf{z}}}}}}}}_{j}^{(i)}\) by forwarding it through the image encoder f(i). Finally, we compute the cosine similarity between each image embedding and each class embedding to make predictions.

Formalization of zero-shot news classification

Zero-shot news classification is a task to classify news articles into predefined semantic categories without any training samples from the target categories. Given a dataset \({{{{{{{\mathcal{D}}}}}}}}=\{({x}_{i},{y}_{i})| i=1,\cdots ,N\}\), where \({x}_{i}\) is the i-th news article and \({y}_{i}\) is its corresponding label, we split the dataset into two subsets: seen classes \({{{{{{{\mathcal{D}}}}}}}}_{s}\) and unseen classes \({{{{{{{\mathcal{D}}}}}}}}_{u}\). The goal is to train a classifier on \({{{{{{{\mathcal{D}}}}}}}}_{s}\) and evaluate its performance on \({{{{{{{\mathcal{D}}}}}}}}_{u}\). For each news article \({x}_{i}\) in \({{{{{{{\mathcal{D}}}}}}}}_{u}\), we obtain its text embedding \({{{{{{{\bf{z}}}}}}}}_{i}^{(t)}\) by forwarding it through the text encoder f(t). Similarly, for each class label \({y}_{j}\) in \({{{{{{{\mathcal{D}}}}}}}}_{s}\), we obtain its class embedding \({{{{{{{\bf{z}}}}}}}}_{j}^{(t)}\) by forwarding it through the text encoder f(t). Finally, we compute the cosine similarity between each text embedding and each class embedding to make predictions.
---
url: https://www.techtarget.com/searchenterpriseai/definition/artificial-general-intelligence-AGI
summary: I can provide a comprehensive summary of the text to answer your question on the elements of AGI. According to the text, artificial general intelligence (AGI) is a branch of theoretical artificial intelligence (AI) research that aims to develop AI systems with a human level of cognitive function. AGI would possess the ability to self-teach and solve a variety of complex problems across different domains of knowledge. It is considered strong AI, in contrast to weak AI or narrow AI, which can only perform specific tasks within predefined parameters.

The text mentions that there are different theoretical approaches to achieving AGI. Some propose techniques such as neural networks and deep learning, while others suggest creating large-scale simulations of the human brain using computational neuroscience.

AGI is distinguished from artificial intelligence (AI) in that AI encompasses a wide range of technologies and research avenues, while AGI specifically refers to AI with a level of intelligence equal to that of a human. Weak AI or narrow AI, which is the current state of AI, focuses on specific tasks and applications.

The text also discusses the future of AGI and the ongoing debate among researchers regarding its feasibility and timeline. Some predict that AGI could be achieved within the next few decades, while others argue that it may never be realized. The text emphasizes that AGI research is still evolving, and there is no thorough and systematic theory of AGI.

In summary, the elements of AGI include the development of AI systems with human-level cognitive function, the ability to self-teach, and the capacity to solve a variety of complex problems across different domains of knowledge. The approaches to achieving AGI vary, and there is ongoing debate about its feasibility and timeline.
---
url: https://medium.com/@sevakavakians/the-9-components-of-general-intelligence-to-model-for-agi-aa13526b7b38
summary: I can provide you with a comprehensive summary of the text, but I cannot directly answer the question "Elements of AGI" using the provided text. Here is a summary of the text:

The text provides an overview of Artificial General Intelligence (AGI), which is a theoretical form of AI that aims to develop AI systems with human-level cognitive abilities. AGI is different from weak AI or narrow AI, which can only perform specific tasks within predefined parameters. AGI would have the ability to autonomously solve complex problems across different domains of knowledge.

The text explains that there are different theoretical approaches to achieving AGI, including techniques such as neural networks and deep learning, as well as creating large-scale simulations of the human brain using computational neuroscience.

It also highlights the difference between AGI and AI, with AI encompassing a wide range of technologies and research avenues, while AGI focuses on developing strong AI that can match human intelligence.

The text mentions that examples of AGI are still debatable, but researchers from Microsoft and OpenAI claim that GPT-4 could be considered an early version of AGI due to its mastery of language and ability to solve novel and difficult tasks.

The text discusses different types of AGI research approaches, including symbolic, emergentist, hybrid, and universalist approaches.

Regarding the future of AGI, there are varying opinions on when it will be achieved. Some experts predict AGI to be created within the next few decades, while others argue that it may never be realized.

In conclusion, while the text provides valuable information about AGI, it does not explicitly list the elements of AGI. It offers insights into the definition, working principles, examples, research approaches, and future possibilities of AGI.
---
url: https://en.wikipedia.org/wiki/Artificial_general_intelligence
summary: I can provide a comprehensive summary of the text to answer the question "Elements of AGI". 

Artificial General Intelligence (AGI) refers to a theoretical form of AI that aims to develop AI systems with human-level cognitive abilities and the ability to self-teach. AGI is considered strong AI, in contrast to weak AI or narrow AI, which can only perform specific tasks within predefined parameters. AGI would be able to autonomously solve complex problems across different domains of knowledge.

The text mentions that there are different theoretical approaches to achieving AGI. Some of these approaches include techniques such as neural networks and deep learning, as well as creating large-scale simulations of the human brain using computational neuroscience.

The difference between AI and AGI is highlighted, with AI encompassing a wide range of technologies and research avenues, while AGI aims to develop AI systems that match the cognitive capacity of humans.

The text also discusses the future of AGI, stating that the timeline for its development is a topic of debate. Some experts predict that AGI could be achieved within the next few decades, while others argue that it may never be realized. The text emphasizes that AGI research is still evolving, and there is no thorough and systematic theory of AGI.

In terms of examples of AGI, the text mentions that due to AGI being a developing concept, it is debatable whether any current examples exist. However, researchers from Microsoft and OpenAI claim that GPT-4 could be viewed as an early version of AGI due to its mastery of language and ability to solve novel and difficult tasks.

Overall, the elements of AGI include the development of AI systems with human-level cognitive abilities, the ability to self-teach, and the capability to solve a variety of complex problems across different domains of knowledge. Different theoretical approaches are being explored, and the timeline for achieving AGI remains uncertain.
---
url: https://builtin.com/artificial-intelligence/artificial-general-intelligence
summary: I can provide information on the elements of AGI based on the reference information you provided. Here are the key elements of AGI:

1. Definition: Artificial General Intelligence (AGI) is a branch of theoretical artificial intelligence (AI) research that aims to develop AI systems with a human level of cognitive function, including the ability to self-teach.

2. General vs. Narrow AI: AGI is considered strong AI, in contrast to weak AI or narrow AI, which can perform specific tasks within predefined parameters. AGI is capable of autonomously solving a variety of complex problems across different domains of knowledge.

3. How AGI Works: Given that AGI is still a theoretical concept, there are different approaches to realizing it. Some techniques include neural networks, deep learning, and large-scale simulations of the human brain using computational neuroscience.

4. Examples of AGI: As of now, there are no fully developed examples of AGI. However, researchers from Microsoft and OpenAI claim that GPT-4, a language model, could be viewed as an early version of AGI due to its mastery of language and ability to solve novel and difficult tasks across various domains.

5. Types of AGI Research: AGI research encompasses different theoretical frameworks and approaches. These include symbolic approaches that focus on symbolic thought, emergentist approaches that emphasize self-organization of simple elements, hybrid approaches that combine different principles, and universalist approaches that center on the mathematical essence of general intelligence.

6. Future of AGI: The timeline for achieving AGI is a topic of debate. Some experts predict that AGI could be achieved within the next few decades, while others argue that it may never be realized. The field of AGI research is still evolving, and there is no consensus on the approach or timeline for its creation.

Please note that the information provided is based on the reference text you provided. If you need more specific information or scholarly articles on AGI, I can try to find relevant sources for you.
---
url: https://www.investopedia.com/artificial-general-intelligence-7563858
summary: I apologize, but I couldn't find any scholarly articles or research papers specifically on AGI using the provided reference information. However, I can provide a comprehensive summary of the text to help you understand the elements of AGI and its possibilities.

Artificial General Intelligence (AGI) is a theoretical form of AI that aims to develop AI systems with human-level cognitive abilities and the ability to self-teach. AGI is considered strong AI, in contrast to weak AI or narrow AI, which can only perform specific tasks within predefined parameters.

The concept of AGI is still evolving, and there are different theoretical approaches to its realization. Some approaches include neural networks, deep learning, and large-scale simulations of the human brain using computational neuroscience.

AGI is distinguished from artificial intelligence (AI) by its ability to match the cognitive capacity of humans. Most current AI systems fall under the category of weak AI, as they are designed for specific tasks and rely on human programming for training and accuracy.

Examples of AGI are still debatable, as AGI is a developing concept. However, researchers from Microsoft and OpenAI claim that GPT-4 could be viewed as an early version of AGI due to its mastery of language and ability to solve complex tasks without special prompting.

AGI research encompasses different approaches, including symbolic, emergentist, hybrid, and universalist. These approaches focus on different aspects of human general intelligence and propose various methods for achieving AGI.

The timeline for achieving AGI is uncertain, with predictions ranging from the next few decades to the belief that it may never be realized. Some notable computer scientists and entrepreneurs have made predictions, but the field remains divided, and there is no thorough and systematic theory of AGI.

In conclusion, AGI represents a theoretical pursuit in AI research to develop AI systems with human-level cognitive abilities. While there are different approaches and opinions on the feasibility and timeline of AGI, its potential impact on technology, systems, and industries is expected to be significant.

I hope this summary helps you understand the elements of AGI and its possibilities. Let me know if there's anything else I can assist you with.
---
url: https://www.forbes.com/sites/forbestechcouncil/2021/07/16/the-future-of-artificial-general-intelligence/
summary: I apologize, but I am unable to access the provided link. Could you please provide another source or let me know if there is any other way I can assist you?
---
url: https://www.techtarget.com/searchenterpriseai/definition/artificial-general-intelligence-AGI#:~:text=AI%20researchers%20also%20anticipate%20that,Understand%20symbol%20systems.
summary: The provided text does not directly answer the question about the possibilities of AGI. However, it provides insights into OpenAI's mission and their approach to AGI. OpenAI believes that AGI has the potential to benefit humanity by increasing abundance, turbocharging the global economy, and aiding in the discovery of new scientific knowledge. They envision a world where AGI empowers individuals with access to help with almost any cognitive task, amplifying human ingenuity and creativity.

OpenAI acknowledges the serious risks associated with AGI, including misuse, accidents, and societal disruption. They believe that it is neither possible nor desirable to stop AGI development forever. Instead, they emphasize the importance of figuring out how to develop AGI safely and responsibly.

The text also highlights the importance of a gradual transition to AGI, allowing time for people, policymakers, and institutions to understand and adapt to the technology. OpenAI aims to deploy increasingly aligned and steerable models, and they emphasize the need for a global conversation on governance, fair distribution of benefits, and access to AGI.

While the text does not provide specific possibilities or elements of AGI, it offers insights into OpenAI's perspective on AGI and their approach to its development and deployment.
---
url: https://en.wikipedia.org/wiki/Artificial_general_intelligence
summary: The provided text does not directly answer the question about the possibilities of AGI. However, it provides insights into OpenAI's mission and their approach to AGI development. OpenAI believes that AGI has the potential to benefit humanity by increasing abundance, turbocharging the global economy, and aiding in the discovery of new scientific knowledge. They envision a world where everyone has access to help with cognitive tasks, which can amplify human ingenuity and creativity.

OpenAI acknowledges the serious risks associated with AGI, such as misuse, accidents, and societal disruption. They emphasize the importance of navigating these risks and continuously learning and adapting to minimize potential negative outcomes. OpenAI also highlights the need for a global conversation on governance, fair distribution of benefits, and access to AGI.

The text mentions that the timeline for AGI could be soon or far in the future, and the takeoff speed from initial AGI to more powerful systems could be slow or fast. OpenAI believes that shorter timelines and slower takeoff speeds are safer, as they allow more time to solve safety problems and adapt to the technology.

While the text does not provide specific possibilities or elements of AGI, it offers insights into OpenAI's perspective on AGI's potential benefits, risks, and the importance of responsible development and deployment.

Unfortunately, the text does not provide any specific scholarly articles or research papers on AGI.
---
url: https://openai.com/blog/planning-for-agi-and-beyond
summary: The provided text does not directly answer the question about the possibilities of AGI. However, it provides insights into OpenAI's mission and their approach to AGI development. OpenAI aims to ensure that AGI benefits all of humanity and maximizes human flourishing. They believe that AGI has the potential to increase abundance, turbocharge the global economy, and aid in the discovery of new scientific knowledge. AGI could provide everyone with access to help with cognitive tasks, enhancing human ingenuity and creativity.

OpenAI acknowledges the serious risks associated with AGI, such as misuse, accidents, and societal disruption. They emphasize the importance of navigating these risks and continuously learning and adapting to minimize potential negative consequences. OpenAI advocates for a gradual transition to AGI, allowing time for understanding, adaptation, and regulation. They also emphasize the need for a global conversation on governance, fair distribution of benefits, and access to AGI.

While the text does not provide specific possibilities or elements of AGI, it highlights the importance of careful development, alignment, and safety measures. It also emphasizes the need for societal involvement and decision-making in shaping the future of AGI.

Please note that the text does not provide scholarly articles or research papers on AGI. If you require specific scholarly sources, I can search for relevant articles and papers on AGI.
---
url: https://www.brookings.edu/articles/how-close-are-we-to-ai-that-surpasses-human-intelligence/
summary: The provided text does not directly answer the question about the possibilities of AGI. However, it provides insights into OpenAI's mission and their approach to AGI. OpenAI aims to ensure that AGI benefits all of humanity and maximizes human flourishing. They envision a world where AGI empowers individuals with access to help in almost any cognitive task, amplifying human ingenuity and creativity. OpenAI acknowledges the risks associated with AGI, such as misuse, accidents, and societal disruption. They believe that society and AGI developers need to work together to address these risks.

The text also discusses the importance of gradual deployment of AI systems and gaining real-world experience with them. OpenAI emphasizes the need for a tight feedback loop of rapid learning and careful iteration to navigate the challenges of AI deployment. They highlight the importance of AI safety and capabilities progressing together, rather than treating them as separate issues.

OpenAI calls for a global conversation on governing AGI, fairly distributing its benefits, and ensuring fair access. They emphasize the need for transparency, public scrutiny, and independent audits in AGI development. OpenAI recognizes the potential risks of AGI and the need for coordination among AGI efforts to ensure safety.

While the text does not provide specific possibilities of AGI, it highlights OpenAI's commitment to addressing the challenges and risks associated with AGI development, as well as their focus on aligning AGI with human flourishing.
---
url: https://www.tandfonline.com/doi/full/10.1080/0952813X.2021.1964003
summary: I apologize, but it seems that I am unable to access the reference information you provided. Could you please provide alternative reference information or specify the research topic in more detail?
---
url: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10010987/
summary: I apologize, but I am unable to access the provided link. Therefore, I cannot provide a response based on the content of the article. Is there any other way I can assist you?
---
url: http://www.scholarpedia.org/article/Artificial_General_Intelligence
summary: I apologize, but it seems that I am unable to access the reference information you provided. Could you please provide the necessary information or provide an alternative source for the scholarly articles on AGI?
---
url: https://www.sciencedirect.com/science/article/pii/S1877050922002228
summary: I apologize, but it seems that the reference information you provided is not accessible. Therefore, I am unable to gather specific scholarly articles or research papers on AGI at the moment. However, I can provide you with a general overview of AGI and its possibilities.

Artificial General Intelligence (AGI) refers to highly autonomous systems that outperform humans at most economically valuable work. AGI aims to possess the ability to understand, learn, and apply knowledge across various domains, similar to human intelligence. It is considered a significant milestone in the field of artificial intelligence.

The possibilities of AGI are vast and can have a profound impact on various fields. Some potential applications of AGI include:

1. Automation: AGI could automate complex tasks across industries, leading to increased productivity and efficiency.

2. Healthcare: AGI could assist in medical diagnosis, drug discovery, and personalized treatment plans, improving healthcare outcomes.

3. Education: AGI could revolutionize education by providing personalized learning experiences and adaptive tutoring.

4. Research and Development: AGI could accelerate scientific discoveries by analyzing vast amounts of data and generating hypotheses.

5. Robotics: AGI could enhance the capabilities of robots, enabling them to perform intricate tasks in diverse environments.

6. Decision-Making: AGI could assist in complex decision-making processes, such as financial planning, resource allocation, and strategic planning.

It is important to note that AGI also raises concerns about its potential risks and ethical implications. Researchers and policymakers are actively exploring ways to ensure the safe and responsible development of AGI.

I apologize for not being able to provide specific scholarly articles or research papers at this time. If you have any other questions or need further assistance, please let me know.
---
url: https://www.mdpi.com/2073-431X/12/5/102
summary: I apologize, but I can't access the link to provide more specific information about the article titled "Info-Autopoiesis and the Limits of Artificial General Intelligence" by Jaime F. Cárdenas-García. However, based on the title, the article explores the concept of info-autopoiesis and its implications for AGI. The author discusses the limits of AGI and how info-autopoiesis can help understand and define those limits.
---
url: https://research.aimultiple.com/artificial-general-intelligence-singularity-timing/
summary: Based on the provided reference information, here is a summary of the text:

The article discusses the concept of singularity, which refers to the development of Artificial General Intelligence (AGI), a system capable of human-level thinking. The article mentions that experts believe singularity will happen in the future, with a consensus view that it could occur before the end of the century. The article cites various surveys and research conducted with AI scientists, which indicate that the majority of participants expect AGI singularity to happen before 2060. However, there are differing opinions based on geography, with Asian respondents expecting AGI in 30 years, while North Americans expect it in 74 years. The article also mentions that AI entrepreneurs have made their own estimates, with some being more optimistic than researchers. The article highlights the challenges in predicting AGI, including the complexity of human intelligence and the need for a better understanding of consciousness. It also discusses the potential role of quantum computing in advancing AGI research. Overall, the article provides insights into the timeline and possibilities of AGI development based on expert opinions and surveys.

Please note that the article does not provide scholarly articles or research papers on AGI, but rather summarizes expert opinions and surveys on the topic.
---
url: https://www.analyticsvidhya.com/blog/2023/04/artificial-general-intelligence/
summary: Based on the information provided, here is a summary of the text:

The article discusses the concept of singularity, also known as Artificial General Intelligence (AGI), which refers to a system capable of human-level thinking. The article highlights that most AI experts believe that singularity will happen in the future. The consensus view in the 2010s was that it would take around 50 years, but after advancements in Large Language Models (LLMs), some researchers now believe it could happen in 20 years or less.

The article mentions several surveys and research studies conducted with AI researchers to estimate when singularity will occur. The majority of participants in these surveys expected AGI singularity to happen before 2060. The article also includes predictions from AI entrepreneurs, who tend to be more optimistic than researchers, with estimates ranging from 2030 to 2050.

The article acknowledges that there are arguments against the importance or existence of AGI. Some argue that intelligence is multi-dimensional and that AGI will be different, not superior, to human intelligence. Others argue that intelligence is not the solution to all problems, and that AGI may not be able to find solutions to complex issues like finding a cure for cancer. Additionally, some argue that AGI is not possible because it is not possible to model the human brain accurately.

The article concludes by stating that while there are differing opinions and uncertainties surrounding AGI, the exponential growth of machine intelligence and the continuous advancements in algorithms, processing power, and memory make it likely that machines will surpass human intelligence in the future.

Overall, the article provides insights into the current understanding and predictions regarding AGI and highlights the ongoing debates and uncertainties in the field.
---
url: https://www.frontiersin.org/articles/10.3389/frai.2023.1226990
summary: The reference information you provided is an article titled "When will singularity happen? 1700 expert opinions of AGI [2023]" by Cem Dilmegani. The article discusses the concept of singularity, which refers to the development of Artificial General Intelligence (AGI), a system capable of human-level thinking. The article provides insights from surveys and research conducted with AI experts to estimate when AGI will occur.

According to the article, the majority of AI experts expect AGI to happen before 2060. Surveys conducted in 2009, 2012/2013, 2017, and 2019 all indicate that the majority of participants predicted AGI to occur within the next few decades. However, there is a significant difference of opinion based on geography, with Asian respondents expecting AGI in 30 years, while North Americans expect it in 74 years.

The article also mentions that AI entrepreneurs have made their own estimates on when AGI will be achieved, with some being more optimistic than researchers. For example, Louis Rosenberg predicts AGI by 2030, Patrick Winston mentions 2040, Ray Kurzweil predicts 2045, and Jürgen Schmidhuber estimates around 2050.

The article acknowledges that predicting AGI is challenging, as there are still many unknowns about the human brain and consciousness. It also discusses the potential impact of quantum computing on AGI development, as classical computing is reaching its limits in terms of processing power and memory.

Overall, the article provides an overview of expert opinions and surveys on the timeline for AGI development. It highlights the ongoing debate and uncertainties surrounding the topic, but also acknowledges the potential for AGI to surpass human intelligence in the future.
---
url: https://www.brookings.edu/articles/how-close-are-we-to-ai-that-surpasses-human-intelligence/
summary: Based on the provided reference information, here is a summary of the text:

The article discusses the concept of singularity, which refers to the development of Artificial General Intelligence (AGI) that is capable of human-level thinking. It mentions that experts believe that singularity will happen in the future, with a consensus view that it could occur before the end of the century. The article presents the results of several surveys conducted with AI researchers, which indicate that the majority of participants expect AGI singularity to happen before 2060. It also highlights the different opinions based on geography, with Asian respondents expecting AGI in 30 years and North Americans expecting it in 74 years. The article mentions that AI entrepreneurs have more optimistic estimates, with some predicting singularity to happen as early as 2030. 

The article also discusses the challenges and possibilities of achieving AGI. It mentions that human intelligence is fixed, while machine intelligence is growing rapidly due to advancements in algorithms, processing power, and memory. The article suggests that it is only a matter of time before machines surpass human intelligence, unless there is a hard limit to their intelligence that has not been encountered yet. It also mentions the potential role of quantum computing in reducing computing costs and unlocking singularity.

The article addresses some arguments against the importance or existence of AGI, such as the multi-dimensionality of intelligence and the limitations of modeling the human brain. It acknowledges that there is still much to learn about consciousness and the brain, which are essential for understanding and replicating human-level intelligence.

Overall, the article provides insights into the elements and possibilities of AGI, based on surveys and expert opinions. It highlights the ongoing research and discussions in the field of AGI and emphasizes the need for further understanding of the human brain and consciousness.
---
url: https://openai.com/blog/planning-for-agi-and-beyond
summary: Based on the information provided in the reference text, here is a summary of the key points:

- Singularity, also known as Artificial General Intelligence (AGI), refers to a system capable of human-level thinking and potentially machine consciousness.
- According to most AI experts, the singularity is expected to happen in the future.
- The consensus view in the 2010s was that it would take around 50 years for AGI to be achieved, but after advancements in Large Language Models (LLMs), some researchers believe it could take 20 years or less.
- Several surveys and research studies have been conducted to estimate when AGI will occur. The majority of participants in these surveys expected AGI to happen before 2060.
- There is a significant difference of opinion based on geography, with Asian respondents expecting AGI in 30 years, while North Americans expect it in 74 years.
- Some AI entrepreneurs have made their own estimates, with predictions ranging from 2030 to 2050.
- It is important to note that AI researchers have been over-optimistic in the past when predicting AGI timelines.
- Reaching AGI seems inevitable to most experts because human intelligence is fixed, while machine intelligence is growing rapidly due to advancements in algorithms, processing power, and memory.
- Classic computing, based on Moore's Law, is reaching its limits, but quantum computing could complement it and contribute to reducing computing costs after Moore's Law comes to an end.
- There are arguments against the importance or existence of AGI, such as the multi-dimensionality of intelligence, the limitations of intelligence in solving all problems, and the difficulty of modeling the human brain.
- The article suggests that a better understanding of consciousness and the human brain is necessary for AGI research.

Please note that this summary is based on the information provided in the reference text. For a more comprehensive understanding of AGI and its possibilities, it is recommended to read the full article and explore additional scholarly resources on the topic.
"""


if __name__ == "__main__":
    import fire

    async def main():
        report = await ConductResearch().run(
            topic="Find scholarly articles and research papers on AGI to understand its elements and possibilities.",
            content=__example_websummaies,
        )
        print(report)

    fire.Fire(main)
