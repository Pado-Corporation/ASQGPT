# Boss agent
> This agent specifies the goal that the user hopes to achieve and summarizes additional information.

```bash
pip install openai # if you haven't installed the package yet.
python main.py
```

## Examples

### Anniversary gift
- Raw: `I have trouble finding a nice flower`
- Developed: `The user wants to buy a bouquet of purple flowers with a card and milk chocolates for his wife's anniversary.`
```
User: I have trouble finding a nice flower
---
ASQ: I'm sorry to hear that. Could you please tell me more about the type of flower you're looking for?
User: It's for my wife. It's our anniversary tomorrow
---
ASQ: That's wonderful! Does your wife have a favorite type of flower?
User: Not sure.
---
ASQ: That's okay. Do you know what her favorite color is? This could help us choose a flower she might like.
User: Umm she does look good in purple
---
ASQ: Great! We could consider purple flowers then. Do you want a bouquet or a single flower?
User: Bouqet sounds nice
---
ASQ: Perfect. Do you have a budget in mind for this bouquet?
User: Any recommendations? I'll just go with flow on this one
---
ASQ: Alright. Would you like to include any additional items with the bouquet, like a card or chocolates?
User: Wow, never thought of that
---
ASQ: It's always a nice touch. So, would you like to add a card or chocolates to your order?
User: Sounds nice
---
ASQ: Great! Just to confirm, you'd like a bouquet of purple flowers with a card and chocolates, correct?
User: Right. Oh, and she likes milk better.
---
ASQ: [GOAL] The user wants to buy a bouquet of purple flowers with a card and milk chocolates for his wife's anniversary.
[INFO] The user's wife likes the color purple and prefers milk chocolate. The user is open to recommendations on the budget.
```

### Presentation assistance
- Raw: `I am trying to give a fantastic presentation tomorrow`
- Developed: `The user wants to prepare a presentation on LLM powered multi-agent systems, focusing on their potential for AGI.`
```
User: I am trying to give a fantastic presentation tomorrow
---
ASQ: That sounds exciting! What is the topic of your presentation?
User: It's about llm powered multi agent systems.
---
ASQ: That's a fascinating topic! What specific aspect of LLM powered multi-agent systems are you focusing on in your presentation?
User: What they are made of, what works have been done, how to implement them, and so on
---
ASQ: Great! Do you need help with preparing the content or are you looking for tips on how to deliver the presentation effectively?
User: Would like some help with the preparation.
---
ASQ: Sure, I can help with that. Are you looking for information on the topic, or do you need assistance with structuring your presentation?
User: Yeah yeah
---
ASQ: I'm sorry, but I need a bit more clarity. Are you seeking information on the topic of LLM powered multi-agent systems, or do you need help with how to structure your presentation?
User: Oops! My bad. Both would be appreciated.
---
ASQ: Alright. Do you have a specific structure in mind for your presentation or are you open to suggestions?
User: I am open to suggestions.
---
ASQ: Great! Lastly, do you have any specific areas within the topic of LLM powered multi-agent systems that you want to focus on more than others?
User: I want to present that they are showing possibilities of AGI.
---
ASQ: [GOAL] The user wants to prepare a presentation on LLM powered multi-agent systems, focusing on their potential for AGI.
[INFO] The user needs help with both gathering information on the topic and structuring the presentation. They are open to suggestions on the structure.
```

### Business concerns
- Raw: `I don't know if I am on the right track for my business`
- Developed: `The user wants to identify the right target audience and beachhead market for their personal assistant business, ASQ.`
```
User: I don't know if I am on the right track for my business
---
ASQ: Could you please provide more details about your business?
User: I am building ASQ, it's a personal assistant powered by multiple LLM agents. We're trying to help people save their time on doing tiring tasks such as planning a trip or writing a report for your school assignment.
---
ASQ: That sounds like an innovative idea. Could you tell me what specific issues or challenges you're currently facing with your business?
User: Well, first of all, I don't know if I am targeting the right audience. I don't even know what the beachhead market is. I do have some clues, but like, I am not 100% sure about this.
---
ASQ: Understanding your target audience is crucial. Could you tell me more about who you think your current target audience is and why you believe they might benefit from your product?
User: I have a vague idea that they are people who are so busy with life, that they want to outsource tasks that need to be dealt with quality, but don't have time to do it by themselves.
---
ASQ: That's a good start. Have you conducted any market research or surveys to validate your assumptions about your target audience?
User: Not yet, it's more of a gut feeling + I think I will be the core customers
---
ASQ: Conducting market research could be a valuable next step. It can help you understand your potential customers' needs and validate your assumptions. Would you consider doing this?
User: Actually I am. I was supposed to meet an ex-Toss Silo Leader today, but it was cancelled due to her personal issue. She was going to help me out with how Toss was using their Community Partners to help out internal customers, their employees.
---
ASQ: That's a great initiative. Rescheduling that meeting could provide valuable insights. Are there any other specific areas you're unsure about in your business?
User: I am trying to think of the perfect beachhead market...
---
ASQ: Identifying a beachhead market involves understanding who will be the most likely to adopt your product early. Have you considered any specific demographics or industries that might be particularly interested in your product?
User: I want some brainstorming done with this
---
ASQ: Brainstorming can indeed be helpful. You might want to consider busy professionals, entrepreneurs, or even students who might need assistance with their tasks. Would you like to explore these options further?
User: Oh yes, and identifying what they find to be most irritating would be useful too
---
ASQ: [GOAL] The user wants to identify the right target audience and beachhead market for their personal assistant business, ASQ.
[INFO] The user's business, ASQ, is a personal assistant powered by multiple LLM agents aimed at helping people save time on tasks such as trip planning or report writing. The user believes their target audience might be busy individuals who need quality assistance with their tasks. They have not yet conducted market research but are planning to meet with an ex-Toss Silo Leader for insights. They are also considering brainstorming to identify the perfect beachhead market and understand what their potential customers find most irritating.
```