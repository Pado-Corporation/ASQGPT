CURRENT_RESEARCHTOOL = [
    {
        "tool": "Google Maps API",
        "WhenToUse": "When geographic or location data and place information such as price is needed",
    },
    {
        "tool": "Google Shopping API",
        "WhenToUse": "When needing to analyze e-commerce trends or product pricing",
    },
    {
        "tool": "Google Trends API",
        "WhenToUse": "When investigating search trends or popularity over time",
    },
    {
        "tool": "Google Product API",
        "WhenToUse": "When looking for specific product details or catalog information",
    },
    {"tool": "Naver API", "WhenToUse": "When needing information from Korean sources or services"},
    {
        "tool": "Walmart API",
        "WhenToUse": "When gathering data on retail products and pricing in Walmart stores",
    },
    {
        "tool": "YouTube Search API",
        "WhenToUse": "When searching for videos or analyzing video metadata",
    },
    {"tool": "Baidu Search API", "WhenToUse": "When needing information from Chinese web sources"},
    {
        "tool": "Google Flight API",
        "WhenToUse": "When researching airfare and flight routes, best tool for flight.",
    },
    {
        "tool": "Google Patent API",
        "WhenToUse": "When investigating patents or intellectual property",
    },
    {
        "tool": "Google Event API",
        "WhenToUse": "When looking for information on public events or calendars",
    },
    {
        "tool": "Google Play Store",
        "WhenToUse": "When analyzing Android app metrics or searching for apps",
    },
    {
        "tool": "Google Scholar",
        "WhenToUse": "When conducting academic research or looking for scholarly articles",
    },
    {"tool": "Websearch", "WhenToUse": "General information gathering"},
]


GoogleMapDescription = (
    """
{
    "api_name": "Google Maps API",
    "api_description": "Our Google Maps API allows you to scrape SERP results from a Google Maps search or places query.",
    "endpoint": "https://serpapi.com/search",
    "request_method": "GET",
    "parameters": [
        {"name": "q", "type": "string", "necessary", "description": "Parameter defines the query you want to search. You can use anything that you would use in a regular Google Maps search. "},
        {"name": "ll", "type": "string", "necessary", "description": "
Parameter defines GPS coordinates of location where you want your q (query) to be applied. It has to be constructed in the next sequence:
@ + latitude + , + longitude + , + zoom

This will form a string that looks like this:
e.g. @40.7455096,-74.0083012,14z. The zoom parameter is optional but recommended for higher precision (it ranges from 3z, map completely zoomed out - to 21z, map completely zoomed in). The parameter should only be used when type is set to search.},
        {"name": "type", "type": "string", "necessary", "option": "search"},
        {"name": "engine", "type": "string", "necessary", "description": "Must be set to 'google_maps'"},
    ],
    "example": https://serpapi.com/search.json?engine=google_maps&q=pizza&ll=@40.7455096,-74.0083012,15.1z&type=search
}

""",
    "local_results",
    "reviews_link",
    "reviews",
)


TOOL_DESCRIPTIONS = {
    "Google Maps API": GoogleMapDescription,  # 이미 있는 GoogleMapDescribe을 사용
    # 다른 도구 설명도 이런 식으로 추가할 수 있습니다.
}


def get_tooldescription(tool_type: str):
    # 입력된 tool_type에 해당하는 설명을 찾아 반환합니다.
    return TOOL_DESCRIPTIONS.get(tool_type, "No tool type exist")
