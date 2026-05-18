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