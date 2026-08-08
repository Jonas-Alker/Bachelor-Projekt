import os
import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD, OWL
import logging

#Getting Logger
logger = logging.getLogger(__name__)

def export_to_turtle(db, output_path):
    """
    Exports the fact-checking data from SQLite into an RDF knowledge graph
    in strict accordance with the Open Claims model.

    :param db: FactCheckManger with data to be exported
    :param output_path: Path for the .ttl (including naming of the file)
    """

    try:
        df = db.get_rdf_export_data()
    except Exception as e:
        logger.error(f"Error loading the database: {e}")
        return

    if df.empty:
        logger.info("No data found for the RDF export.")
        return

    logger.info("Start Building RDF export")
    g = Graph()

    # vocabulary from the diagram
    SCHEMA = Namespace("https://schema.org/")
    OA = Namespace("http://www.w3.org/ns/oa#")
    MARL = Namespace("http://purl.org/marl/ns#")
    PROV = Namespace("http://www.w3.org/ns/prov#")
    NIF = Namespace("http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#")

    CKG = Namespace("http://data.gesis.org/claimskg/")

    g.bind("schema", SCHEMA)
    g.bind("oa", OA)
    g.bind("marl", MARL)
    g.bind("prov", PROV)
    g.bind("nif", NIF)
    g.bind("ckg", CKG)
    g.bind("owl", OWL)


    for index, row in df.iterrows():

        # Generate URIs for the instances
        proposition_uri = CKG[f"proposition_{row['claim_id']}"]
        utterance_uri = CKG[f"utterance_{row['claim_id']}"]
        context_uri = CKG[f"context_{row['claim_id']}"]
        review_uri = CKG[f"review_{row['review_id']}_{row['claim_id']}"] #This string concatenation is necessary because a claim can have several ratings
        portal_uri = CKG[f"portal_{row['portal_id']}"]

        g.add((proposition_uri, RDF.type, SCHEMA.Intangible))
        g.add((utterance_uri, RDF.type, SCHEMA.Claim))
        g.add((utterance_uri, SCHEMA.about, proposition_uri))
        g.add((utterance_uri, SCHEMA.about, context_uri))

        #Utterance
        if pd.notna(row['claim']):
            ling_repr_uri = CKG[f"linguistic_repr_{row['claim_id']}"]
            g.add((ling_repr_uri, RDF.type, SCHEMA.Text))
            g.add((ling_repr_uri, SCHEMA.text, Literal(row['claim'], lang=row['language'])))
            g.add((utterance_uri, CKG.hasLinguisticRepresentation, ling_repr_uri))

        #Context
        g.add((context_uri, RDF.type, SCHEMA.Intangible))
        if pd.notna(row['claim_author']):
            author_uri = CKG[f"person_{hash(row['claim_author'])}"]
            g.add((author_uri, RDF.type, SCHEMA.Person))
            g.add((author_uri, SCHEMA.name, Literal(row['claim_author'])))
            g.add((context_uri, SCHEMA.agent, author_uri))

        if pd.notna(row['stated_at']):
            try:
                formatted_date = pd.to_datetime(row['stated_at'], dayfirst=True).strftime('%Y-%m-%d')
                g.add((context_uri, SCHEMA.dateCreated, Literal(formatted_date, datatype=XSD.date)))
            except Exception:
                g.add((context_uri, SCHEMA.dateCreated, Literal(str(row['stated_at']))))
        #Review
        g.add((review_uri, RDF.type, SCHEMA.ClaimReview))
        g.add((review_uri, SCHEMA.itemReviewed, proposition_uri))

        if pd.notna(row['headline']):
            g.add((review_uri, SCHEMA.headline, Literal(row['headline'], lang=row['language'])))

        if pd.notna(row['article_url']):
            g.add((review_uri, SCHEMA.url, URIRef(row['article_url'])))

        if pd.notna(row['rating_original']):
            rating_uri = CKG[f"rating_{row['review_id']}_{row['claim_id']}"] #This string concatenation is necessary because a claim can have several ratings
            g.add((rating_uri, RDF.type, SCHEMA.Rating))
            g.add((rating_uri, SCHEMA.name, Literal(row['rating_original'], lang=row['language'])))
            g.add((review_uri, SCHEMA.reviewRating, rating_uri))

        g.add((portal_uri, RDF.type, SCHEMA.Organization))
        if pd.notna(row['portal_name']):
            g.add((portal_uri, SCHEMA.name, Literal(row['portal_name'])))

        g.add((review_uri, SCHEMA.author, portal_uri))

    # Export
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    g.serialize(destination=output_path, format="turtle")
    logger.info(f"Exported {len(df)} rows to {output_path}")
