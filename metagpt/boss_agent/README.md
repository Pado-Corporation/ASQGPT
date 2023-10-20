# Boss agent

> This agent specifies the goal that the user hopes to achieve.

### Example

```commandline
$ python main.py "I'm having troubling choosing a flower"
ASQ: I see. Can you tell me what the flower is for?
User: Anniversary
ASQ: That's lovely. Do you know if the person you're giving the flower to has any favorite flowers?
User: Sunflowers? tbh I rly don't know
ASQ: That's okay. Do you have any color preferences for the flower?
User: Well, it's for my wife so she better like it. I don't know about that either
ASQ: Understood. Do you want a single flower or a bouquet?
User: the latter
ASQ: Great. Do you have a budget in mind for the bouquet?
User: around $80 
ASQ: Alright. Do you want the bouquet to be delivered or will you pick it up yourself?
User: delivery would be nice
ASQ: Perfect. Do you have a specific date you want the bouquet to be delivered?
User: By next Friday
ASQ: Okay. Lastly, would you like to include a message with the bouquet?
User: That's thoughtful
ASQ: [GOAL] The user wants to order a sunflower bouquet for his wife for their anniversary, with a budget of around $80. The bouquet should be delivered by next Friday and include a thoughtful message.
```
