from SPARQLWrapper import SPARQLWrapper, JSON



def get_urls_from_claimskg(source_name):
    sparql = SPARQLWrapper("https://data.gesis.org/claimskg/sparql")

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
               schema:author <http://data.gesis.org/claimskg/organization/{portal}> .
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