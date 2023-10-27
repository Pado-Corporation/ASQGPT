from metagpt.logs import logger

NOTSURE_RESEARCHTOOL = [
    {
        "tool": "Google Scholar API",
        "WhenToUse": "When looking for research or looking for scholarly articles",
    },
    {"tool": "Naver API", "WhenToUse": "When needing information from Korean sources or services"},
    {"tool": "Baidu Search API", "WhenToUse": "When needing information from Chinese web sources"},
    {
        "tool": "Google Patent API",
        "WhenToUse": "When investigating patents or intellectual property",
    },
    {
        "tool": "Google Play Store",
        "WhenToUse": "When analyzing Android app metrics or searching for apps",
    },
    {
        "tool": "Google Trends by Region API",
        "WhenToUse": "When investigating search trends by region",
    },
]

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
        "tool": "Google Jobs API",
        "WhenToUse": "When needing to find about job information.",
    },
    {
        "tool": "Google News API",
        "WhenToUse": "When needing to find an information in the news.",
    },
    {
        "tool": "Google Trends API",
        "WhenToUse": "When investigating search trends or popularity over time",
    },
    {
        "tool": "Google Finance STOCK API",
        "WhenToUse": "Our Google Finance API allows you to scrape stock price data from the Google Finance page",
    },
    {
        "tool": "Google Finance News and Financials API",
        "WhenToUse": "Our Google Finance API allows you to scrape Financial news and Financial data like balance sheet data from the Google Finance page",
    },
    {
        "tool": "Walmart API",
        "WhenToUse": "When gathering data on retail products and pricing in Walmart stores",
    },
    {
        "tool": "YouTube Search API",
        "WhenToUse": "When searching for videos or analyzing video metadata",
    },
    {
        "tool": "Google Flight API",
        "WhenToUse": "When researching airfare and flight routes, best tool for flight.",
    },
    {
        "tool": "Google Event API",
        "WhenToUse": "When looking for information on public events or calendars",
    },
    {
        "tool": "WEBSEARCH",
        "WhenToUse": "General information gathering by crawling. Use it in necessary situation",
    },
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
        {"name": "ll", "type": "string", "necessary", "description": " Parameter defines GPS coordinates of location where you want your q (query) to be applied. 
        It has to be constructed in the next sequence: @ + latitude + , + longitude + , + zoom 
        This will form a string that looks like this: e.g. @40.7455096,-74.0083012,14z. The zoom parameter is optional but recommended for higher precision (it ranges from 3z, map completely zoomed out - to 21z, map completely zoomed in). The parameter should only be used when type is set to search.},
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

GoogleShoppingDescription = (
    """
{
    "api_name": "Google Shopping API",
    "api_description": "Our Google Shpping API allows you to scrape SERP results from a Google Shopping search query.",
    "endpoint": "https://serpapi.com/search",
    "request_method": "GET",
    "parameters": [
        {"name": "q", "type": "string", "necessary", "description": "Parameter defines the query you want to search. You can use anything that you would use in a regular Google Shopping search. "},
        {"name": "engine", "type": "string", "necessary", "description": "Must be set to 'google_shopping'"},
    ],
    "example": https://serpapi.com/search.json?engine=google_shopping&q=Macbook+M2
}

""",
    "shopping_results",
    "serpapi_product_api",
    "reviews",
)

GoogleJobDescriontion = (
    """
{
    "api_name": "Google Jobs API",
    "api_description": "Our Google Jobs API allows you to scrape SERP results from a Google Jobs search query.",
    "endpoint": "https://serpapi.com/search",
    "request_method": "GET",
    "parameters": [
        {"name": "q", "type": "string", "necessary", "description": "Parameter defines the query you want to search. You can use anything that you would use in a regular Google Jobs search. "},
        {"name": "engine", "type": "string", "necessary", "description": "Must be set to 'google_jobs'"},
        {"name": "location", "type": "string", "optional", "description": "Parameter defines from where you want the search to originate. If several locations match the location requested, we'll pick the most popular one. It is recommended to specify location at the city level in order to simulate a real user’s search. If location is omitted, the search may take on the location of the proxy."},
    ],
    "example": https://serpapi.com/search.json?engine=google_jobs&q=barista+new+york&location=Newyork
}

""",
    "jobs_results",
    None,
    None,
)

GoogleNewsDescription = (
    """
{
    "api_name": "Google News API",
    "api_description": "Our Google Jobs API allows you to scrape SERP results from a Google Jobs search query.",
    "endpoint": "https://serpapi.com/search",
    "request_method": "GET",
    "parameters": [
        {"name": "q", "type": "string", "necessary", "description": "Parameter defines the query you want to search. You can use anything that you would use in a regular Google News search. "},
        {"name": "tbm", "type": "string", "necessary", "description": "Must be set to 'nws'"},
        {"name": "location", "type": "string", "optional", "description": "Parameter defines from where you want the search to originate. If several locations match the location requested, we'll pick the most popular one. It is recommended to specify location at the city level in order to simulate a real user’s search. If location is omitted, the search may take on the location of the proxy."},
            ],
    "example": https://serpapi.com/search.json?q=Biden&tbm=nws&location=Austin,+TX,+Texas,+United+States
}

""",
    "news_results",
    "link",
    None,
)

GoogleTrendsbyRegionDescription = (
    """
{
    "api_name": "Google Trends by Region API",
    "api_description": "Our Google Trends API allows you to scrape SERP results from a Google Trends by search query by region",
    "endpoint": "https://serpapi.com/search",
    "request_method": "GET",
    "parameters": [
        {"name": "q", "type": "string", "necessary", "description": "Parameter defines the query you want to search. You can use anything that you would use in a regular Google Trends search. "},
        {"name": "engine", "type": "string", "necessary", "description": "Set parameter to google_trends to use the Google Trends by Region API engine."},
        {"name": "data_type", "type": "string", "necessary", "description": "Set parameter to GEO_MAP to use the Google Trends by Region API engine."}
        {"name": "region", "type": "singleselect", "Optional", "description": "Parameter is used for getting more specific results Available options:

COUNTRY - Country
REGION - Subregion
DMA - Metro
CITY - City"}

    ],
    "example": https://serpapi.com/search.json?engine=google_trends&q=coffee,milk,bread,pasta,steak&data_type=GEO_MAP&data_type=COUNTRY
}

""",
    "compared_breakdown_by_region",
    None,
    None,
)

GoogleTrendsDescription = (
    """
{
    "api_name": "Google Trends API",
    "api_description": "Our Google Trends API allows you to scrape SERP results from a Google Trends by search query as time series",
    "endpoint": "https://serpapi.com/search",
    "request_method": "GET",
    "parameters": [
        {"name": "q", "type": "string", "necessary", "description": "Parameter defines the query you want to search. You can use anything that you would use in a regular Google Trends search. "},
        {"name": "engine", "type": "string", "necessary", "description": "Set parameter to google_trends to use the Google Trends API engine."},
        {"name": "data_type" , "description": "must set to TIMESERIES"}
        {"name": "date", "necessary", "description" : "
Parameter is used to define a date. Available options:

now 1-H - Past hour
now 4-H - Past 4 hours
now 1-d - Past day
now 7-d - Past 7 days
today 1-m - Past 30 days
today 3-m - Past 90 days
today 12-m - Past 12 months
all - 2004 - present You can also pass custom values:

Dates from 2004 to present: yyyy-mm-dd yyyy-mm-dd (e.g. 2021-10-15 2022-05-25)
Dates with hours within a week range: yyyy-mm-ddThh yyyy-mm-ddThh (e.g. 2022-05-19T10 2022-05-24T22). Hours will be calculated depending on the tz (time zone) parameter."}
    ],
    "example": https://serpapi.com/search.json?engine=google_trends&q=coffee,milk,bread,pasta,steak&data_type=TIMESERIES
}

""",
    "interest_over_time.timeline_data",
    None,
    None,
)

GoogleFinanceStockDescription = (
    """
{
    "api_name": "Google Finance API",
    "api_description": "Our Google Finance API allows you to scrape SERP results from a Google Finance by search query as time series",
    "endpoint": "https://serpapi.com/search",
    "request_method": "GET",
    "parameters": [
        {"name": "q", "type": "string", "necessary", "description": "Parameter defines the query you want to search. You can use anything that you would use in a regular Google Finance search. If you want to search something, you should make it in searchquery:market form. example: NASDAQ:GOOG, GCW00:COMEX, NYSE: SHOP "},
        {"name": "engine", "type": "string", "necessary", "description": "Set parameter to google_finance to use the Google Finance API engine."},
        {"name": "window", "type": "string", "optional", "5D - 5 Days, 1M - 1 Month, 6M - 6 Months, YTD - Year to Date, 1Y - 1 Year, 5Y - 5 Years, MAX - Maximum"}
    ],
    "example": https://serpapi.com/search.json?engine=google_finance&q=GOOG:NASDAQ&window=5D
}

""",
    "graph",
    None,
    None,
)

GoogleFinanceFinancialDescription = (
    """
{
    "api_name": "Google Finance API",
    "api_description": "Our Google Finance API allows you to scrape SERP results from a Google Finance by search query as time series",
    "endpoint": "https://serpapi.com/search",
    "request_method": "GET",
    "parameters": [
        {"name": "q", "type": "string", "necessary", "description": "Parameter defines the query you want to search. You can use anything that you would use in a regular Google Finance search. If you want to search something, you should make it in searchquery:market form. example: NASDAQ:GOOG, GCW00:COMEX, NYSE: SHOP "},
        {"name": "engine", "type": "string", "necessary", "description": "Set parameter to google_finance to use the Google Finance API engine."},
    ],
    "example": https://serpapi.com/search.json?engine=google_finance&q=GOOG:NASDAQ
}

""",
    ["news_results", "financials"],
    None,
    None,
)


GoogleScholarDescription = (
    """
{
    "api_name": "Google Scholar API",
    "api_description": "Our Google Scholar API allows you to scrape SERP results from a Google Scholar by search query as time series",
    "endpoint": "https://serpapi.com/search",
    "request_method": "GET",
    "parameters": [
        {"name": "q", "type": "string", "necessary", "description": "Parameter defines the query you want to search. You can use anything that you would use in a regular Google Scholar search. "},
        {"name": "engine", "type": "string", "necessary", "description": "Set parameter to google_scholar to use the Google scholar API engine."},
    ],
    "example": https://serpapi.com/search.json?engine=google_scholar&q=biology
}

""",
    "organic_results",
    None,
    None,
)


WalmartDescription = (
    """
{
    "api_name": "Walmart API",
    "api_description": "Our Walmart API allows you to scrape SERP results from a Walmart by search query ",
    "endpoint": "https://serpapi.com/search",
    "request_method": "GET",
    "parameters": [
        {"name": "query", "type": "string", "necessary", "description": "Parameter defines the query you want to search. You can use anything that you would use in a regular Walmart search. "},
        {"name": "engine", "type": "string", "necessary", "description": "Set parameter to walmart to use the Walmart API engine."},
    ],
    "example": https://serpapi.com/search.json?engine=walmart&query=Coffee
}

""",
    "organic_results",
    "product_id",
    "reviews",
)

YoutubeSearchDescription = (
    """
{
    "api_name": "YouTube Search API",
    "api_description": "Our YouTube Search API allows you to scrape SERP results from a Youtube by search query ",
    "endpoint": "https://serpapi.com/search",
    "request_method": "GET",
    "parameters": [
        {"name": "search_query", "type": "string", "necessary", "description": "Parameter defines the query you want to search. You can use anything that you would use in a regular Youtube search. "},
        {"name": "engine", "type": "string", "necessary", "description": "Set parameter to youtube to use the Youtube API engine."},
    ],
    "example": https://serpapi.com/search.json?engine=youtube&search_query=star+wars
}

""",
    "video_results",
    None,
    None,
)

GoogleFlightDescription = (
    """
{
    "api_name": "Google Flight API",
    "api_description": "Our Google Flight API allows you to scrape SERP results from a googleflight",
    "endpoint": "https://serpapi.com/search",
    "request_method": "GET",
    "parameters": [
        {"name": "type", "options": "1 - Round trip , 2 - One way"}
        {"name": "departure_id", "type": "string", "necessary", "description": " Parameter defines the departure airport code or city ID.An airport code is an uppercase 3-letter code. based on Google Flights or IATA For example, CDG is Paris Charles de Gaulle Airport and AUS is Austin-Bergstrom International Airport."},
        {"name": "engine", "type": "string", "necessary", "description": "Set parameter to google_flight to use the googleflight API engine."},
        {"name": "arrival_id", "type": "string", "optional", "description": " Parameter defines the arrival airport code or city ID.An airport code is an uppercase 3-letter code. based on Google Flights or IATA For example, CDG is Paris Charles de Gaulle Airport and AUS is Austin-Bergstrom International Airport. if it is one way trip then do not input this parameter"},
        {"name": "outbound_date", "type": "string", "necessary", "description": "Parameter defines the outbound date. The format is YYYY-MM-DD. e.g. 2023-10-24"},
        {"name": "return_date", "type": "string", "optional", "description": " Parameter defines the return date. The format is YYYY-MM-DD. e.g. 2023-10-30 Parameter is required if type parameter is set to: 1 (Round trip)"},
    ],
    "example": https://serpapi.com/search.json?engine=google_flights&departure_id=PEK&arrival_id=AUS&outbound_date=2023-10-25&return_date=2023-10-31&currency=USD&hl=en
}

""",
    "best_flights",
    None,
    None,
)

GoogleEventDescription = (
    """
{
    "api_name": "Google Event API",
    "api_description": "Our Google Event API allows you to scrape SERP results from a Google Event by search query ",
    "endpoint": "https://serpapi.com/search",
    "request_method": "GET",
    "parameters": [
        {"name": "q", "type": "string", "necessary", "description": "Parameter defines the query you want to search. To search for events in a specific location, just include the location inside your search query (e.g. Events in Austin, TX)."},
        {"name": "engine", "type": "string", "necessary", "description": "Set parameter to google_events to use the google_events API engine."},
    ],
    "example": https://serpapi.com/search.json?engine=google_events&q=Events+in+Austin&hl=en&gl=us
}

""",
    "events_results",
    "link",
    None,
)

TOOL_DESCRIPTIONS = {
    "Google Maps API": GoogleMapDescription,  # 이미 있는 GoogleMapDescribe을 사용
    "Google Shopping API": GoogleShoppingDescription,
    "Google Jobs API": GoogleJobDescriontion,
    "Google News API": GoogleNewsDescription,
    "Google Trends API": GoogleTrendsDescription,
    "Google Trends by Region API": GoogleTrendsbyRegionDescription,
    "Google Finance STOCK API": GoogleFinanceStockDescription,
    "Google Finance News and Financials API": GoogleFinanceFinancialDescription,
    "Google Scholar API": GoogleScholarDescription,
    "Walmart API": WalmartDescription,
    "YouTube Search API": YoutubeSearchDescription,
    "Google Flight API": GoogleFlightDescription,
    "Google Event API": GoogleEventDescription,
}


def get_tooldescription(tool_type: str):
    # 입력된 tool_type에 해당하는 설명을 찾아 반환합니다.
    description = TOOL_DESCRIPTIONS.get(tool_type)
    if description is None:
        logger.error(f"No tool type exists for {tool_type}")
        return "No tool type exist"
    return description
