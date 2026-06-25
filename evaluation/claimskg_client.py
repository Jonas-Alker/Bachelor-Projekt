from SPARQLWrapper import SPARQLWrapper, JSON

def get_urls_from_claimskg(source_name,year_start= None, year_end= None):
    """Fetches a unique set of fact-checking URLs from ClaimsKG via a SPARQL query
    The queries can be optionally filtered by a publication year range (start year,
    end year, or both).

    :param source_name: The name of the fact-checking portal.
    :param year_start: The optional starting year for filtering results
    :param year_end: The optional ending year for filtering results

    :return: A set of unique URL strings retrieved from the ClaimsKG platform.
        Returns an empty set if no results are found or if an error occurs.
    """
    sparql = SPARQLWrapper("https://data.gesis.org/claimskg/sparql")
    date_filter = ""

    if year_start and year_end:
        date_filter = f"""
        schema:datePublished ?date BIND (year(?date) AS ?year)FILTER(?year >= {year_start} && ?year <= {year_end})
    """

    if year_start and not year_end:
        date_filter = f"""
           schema:datePublished ?date BIND (year(?date) AS ?year)FILTER(?year >= {year_start})
       """

    if not year_start and year_end:
        date_filter = f"""
             schema:datePublished ?date BIND (year(?date) AS ?year)FILTER(?year <= {year_end})
         """

    prefix= """
    PREFIX schema: <http://schema.org/>
    PREFIX claimskg: <http://data.gesis.org/claimskg/vocab/>
    PREFIX bp: <http://data.gesis.org/claimskg/blueprint/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX dbr: <http://dbpedia.org/resource/>
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    """
    portal = source_name.lower()
    sparql_query = prefix + f"""
    SELECT DISTINCT ?url WHERE {{
    ?claimReview a schema:ClaimReview ;
               schema:url ?url ;
               schema:author <http://data.gesis.org/claimskg/organization/{portal}>;
               {date_filter}.
    }}
    """

    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)

    try:
        results = sparql.query().convert()
        if"results" in results and "bindings" in results["results"]:
            urls = [result["url"]["value"] for result in results["results"]["bindings"]]
            return set(urls)
        else:
            print("No urls in JSON from Claimskg")
            return set()
    except Exception as e:
        print(f"Error at SPARQL query: {e}")
        return set()

def get_claim_details_by_url(url):
    """
    Fetches all relevant metadata for a fact-checking article based on its URL.

    :param article_url: The URL of the fact-checking article

    :return: A dictionary containing the extracted data (or ‘N/A’ if none is available).
    """
    sparql = SPARQLWrapper("https://data.gesis.org/claimskg/sparql")

    prefix = """
       PREFIX schema: <http://schema.org/>
       PREFIX claimskg: <http://data.gesis.org/claimskg/vocab/>
       PREFIX bp: <http://data.gesis.org/claimskg/blueprint/>
       PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
       PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
       PREFIX dbr: <http://dbpedia.org/resource/>
       PREFIX dbo: <http://dbpedia.org/ontology/>
       PREFIX owl: <http://www.w3.org/2002/07/owl#>
       """

    sparql_query = prefix + f"""
        SELECT 
            ?portal_name ?portal_url ?headline ?published 
            ?language ?rating_original ?claim_text 
            ?claim_author ?stated_at
        WHERE {{
            ?claimReview a schema:ClaimReview ;
                         schema:url ?url .
            FILTER(str(?url) = "{url}")

            OPTIONAL {{ ?claimReview schema:headline ?headline . }}
            OPTIONAL {{ ?claimReview schema:datePublished ?published . }}
            OPTIONAL {{ ?claimReview schema:inLanguage ?language . }}
            OPTIONAL {{
                ?claimReview schema:author ?portalNode .
                OPTIONAL {{ ?portalNode schema:name ?portal_name . }}
                OPTIONAL {{ ?portalNode schema:url ?portal_url . }}
                }}
            OPTIONAL {{ 
                ?claimReview schema:reviewRating ?ratingNode .
                ?ratingNode schema:alternateName ?rating_original . }}
            OPTIONAL {{
                ?claimReview schema:itemReviewed ?claimNode .
                OPTIONAL {{ ?claimNode schema:text ?claim_text . }}

                OPTIONAL {{ 
                    ?claimNode schema:author ?cAuthor .
                    OPTIONAL {{ ?cAuthor schema:name ?claim_author . }}
                }}

                OPTIONAL {{ ?claimNode schema:datePublished ?stated_at . }}
            }}
        }}
        """

    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)

    details = {
        "portal_name": "N/A",
        "portal_url": "N/A",
        "headline": "N/A",
        "published_at": "N/A",
        "article_url": url,
        "article_author": "N/A",
        "language": "N/A",
        "rating_original": "N/A",
        "claim": "N/A",
        "claim_author": "N/A",
        "stated_at": "N/A"
    }
    all_claims = []
    try:
        results = sparql.query().convert()
        bindings = results.get("results", {}).get("bindings", [])

        if bindings:
            for data in bindings:
                details = {
                    "portal_name": data.get("portal_name", {}).get("value", "N/A"),
                    "portal_url": data.get("portal_url", {}).get("value", "N/A"),
                    "headline": data.get("headline", {}).get("value", "N/A"),
                    "published_at": data.get("published", {}).get("value", "N/A"),
                    "article_url": url,
                    "article_author": "N/A",
                    "language": data.get("language", {}).get("value", "N/A"),
                    "rating_original": data.get("rating_original", {}).get("value", "N/A"),
                    "claim": data.get("claim_text", {}).get("value", "N/A"),
                    "claim_author": data.get("claim_author", {}).get("value", "N/A"),
                    "stated_at": data.get("stated_at", {}).get("value", "N/A")
                }
                all_claims.append(details)
        else:
            print(f"No data found in ClaimsKG for the URL: {url}")

        return all_claims

    except Exception as e:
        print(f"Error in the SPARQL query for: {url}: {e}")
        return all_claims