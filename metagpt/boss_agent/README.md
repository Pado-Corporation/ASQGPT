# Boss agent
> This agent specifies the goal that the user hopes to achieve and summarizes additional information.

## Examples

### Anniversary gift
- Raw: `I have trouble finding a nice flower`
- Developed: `The user wants to buy a bouquet of purple flowers with a card and milk chocolates for his wife's anniversary.`
```
python main.py "I have trouble finding a nice flower"
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
$ python main.py "I am trying to give a fantastic presentation tomorrow"
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