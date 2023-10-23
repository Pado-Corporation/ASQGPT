import openai
from metagpt.config import CONFIG


openai.api_key = CONFIG.openai_api_key

dataset = [
    """The market for acne patches has been growing in recent years, driven by the increasing interest in skincare products that are gentle and non-invasive. Acne patches are seen as a more effective and convenient alternative to traditional acne treatments like creams and gels. They are particularly popular among those who prefer to avoid harsh chemicals. This report aims to provide an overview of the trend of acne patches in the market by analyzing various sources of information.
## References
1. Grand View Research. (n.d.). Anti-acne Dermal Patch Market Size, Share & Trends Analysis Report. Retrieved from [https://www.grandviewresearch.com/industry-analysis/anti-acne-dermal-patch-market](https://www.grandviewresearch.com/industry-analysis/anti-acne-dermal-patch-market)
2. Fact.MR. (n.d.). Anti-acne Dermal Patch Market. Retrieved from [https://www.factmr.com/report/anti-acne-dermal-patch-market](https://www.factmr.com/report/anti-acne-dermal-patch-market)
3. Inkwood Research. (n.d.). Anti-acne Dermal Patch Market. Retrieved from [https://inkwoodresearch.com/reports/anti-acne-dermal-patch-market/](https://inkwoodresearch.com/reports/anti-acne-dermal-patch-market/)
4. The Brainy Insights. (n.d.). Anti-acne Dermal Patch Market. Retrieved from [https://www.thebrainyinsights.com/report/anti-acne-dermal-patch-market-12669](https://www.thebrainyinsights.com/report/anti-acne-dermal-patch-market-12669)
""",
    """## Market Overview
The global anti-acne dermal patch market size was valued at USD 510.8 million in 2021 and is expected to grow at a compound annual growth rate (CAGR) of 6.1% from 2022 to 2030 [1]. The market is driven by the rising incidence of skin conditions such as severe acne and pimples, as well as the increasing demand for instant acne treatment and medication. Acne patches are filled with active ingredients such as tea tree oil and salicylic acid, which help eliminate acne-causing bacteria and reduce inflammation [9].
## References
1. Grand View Research. (n.d.). Anti-acne Dermal Patch Market Size, Share & Trends Analysis Report. Retrieved from [https://www.grandviewresearch.com/industry-analysis/anti-acne-dermal-patch-market](https://www.grandviewresearch.com/industry-analysis/anti-acne-dermal-patch-market)
2. Fact.MR. (n.d.). Anti-acne Dermal Patch Market. Retrieved from [https://www.factmr.com/report/anti-acne-dermal-patch-market](https://www.factmr.com/report/anti-acne-dermal-patch-market)
3. Inkwood Research. (n.d.). Anti-acne Dermal Patch Market. Retrieved from [https://inkwoodresearch.com/reports/anti-acne-dermal-patch-market/](https://inkwoodresearch.com/reports/anti-acne-dermal-patch-market/)
4. The Brainy Insights. (n.d.). Anti-acne Dermal Patch Market. Retrieved from [https://www.thebrainyinsights.com/report/anti-acne-dermal-patch-market-12669](https://www.thebrainyinsights.com/report/anti-acne-dermal-patch-market-12669)
""",
    """## Market Dynamics
Several factors contribute to the growing trend of acne patches in the market:

1. Increasing Awareness about Skincare: There is a rising awareness about the benefits of maintaining healthy and clear skin. Consumers are seeking non-invasive and gentle solutions to acne, and acne patches fit the bill perfectly [2][3].

2. Preference for Natural Ingredients: There is a growing preference for skincare products that contain natural ingredients. Acne patches that contain ingredients like tea tree oil, witch hazel, and aloe vera are particularly popular [2][3].

3. Rise of E-commerce: The growth of e-commerce has allowed consumers to access a wider range of acne patch products than ever before. This has also enabled brands to reach a global audience and expand their customer base [2][3].

4. Intense Competition: The acne patch market is highly competitive, with a large number of established brands and new entrants vying for market share. Companies are investing in innovative marketing strategies, unique ingredients, and eye-catching packaging to differentiate themselves from their competitors [2][3].

5. Rising Demand for Eco-friendly Products: There is a growing demand for eco-friendly skincare options. Consumers are becoming more conscious of their environmental impact and are looking for products that use sustainable materials and packaging [2][3].

6. Changing Consumer Demographics: The demographics of the acne patch market are changing, with an aging population and increasing awareness about skincare among men. Brands are diversifying their product lines to cater to different age groups and gender demographics [2][3].

7. Impact of COVID-19: The COVID-19 pandemic has affected the acne patch market, causing disruptions in supply chains, changes in consumer behavior, and a shift towards online shopping. However, the market is expected to rebound as the pandemic subsides [2][3].""",
    """## AI Agents: Overview and Types
AI agents are composed of four main components: the environment, sensors, actuators, and the decision-making mechanism. The environment refers to the domain in which the AI agent operates, while sensors perceive the environment and actuators interact with it. The decision-making mechanism processes sensor data to determine the appropriate actions to achieve the agent's goals.

There are different types of AI agents, including simple reflex agents, model-based reflex agents, goal-based agents, utility-based agents, and learning agents. Each type has its own characteristics and capabilities, enabling them to perform specific tasks effectively.""",
]

embeddings = []

for sentence in dataset:
    response = openai.Embedding.create(model="text-embedding-ada-002", input=[sentence])
    embeddings.append((sentence, response["data"][0]["embedding"], {}))


import vecs

DB_CONNECTION = CONFIG.db_addr

# create vector store client
vx = vecs.Client(DB_CONNECTION)

# create a collection named 'sentences' with 1536 dimensional vectors (default dimension for text-embedding-ada-002)
sentences = vx.get_or_create_collection(name="test", dimension=1536)

# upsert the embeddings into the 'sentences' collection
sentences.upsert(records=embeddings)

# create an index for the 'sentences' collection
sentences.create_index()

query_sentence = "demand forcast acne patch"

# create an embedding for the query sentence
response = openai.Embedding.create(model="text-embedding-ada-002", input=[query_sentence])
query_embedding = response["data"][0]["embedding"]

# query the 'sentences' collection for the most similar sentences
results = sentences.query(data=query_embedding, limit=4, include_value=True)

# print the results
for result in results:
    print(result)
