# README: Refactoring Search

This directory of code had incremental progress on refactoring Open Context's search functionality.

This does nothing to change the existing search features. It is a new project to attempt to make the 
existing convoluted, complicated, obscure and highly redundant code into something that is easier to 
understand and maintain.

## General architecture
Open Context defines a very abstract and not particularly user-friendly schema for indexing documuents
(all the Manifest items) in Solr. We have lots of abstraction in the solr schema because we have to
ingest data from different projects, all of which have their own descriptive attributes and controlled
vocabularies. So Open Context uses a very abstract Solr schema, with many, many dynamic fields to
represent the schemas of different project datasets.

To make this abstraction easier to work with, Open Context does the following:

- Open Context has a query syntax that it exposes to the outside world for clients to use 
(see: https://opencontext.org/about/services#tab_query-syntax). Open Context translates requests from
outside clients into a query uses solr's query syntax and (super abstract) schema.
- Solr response with results in the form of a big JSON-encoded dictionary object. Open Context then
translates these Solr results into different output options, defaulting to a JSON-LD + GeoJSON 
output. 
- To make things easier for clients, Open Context's default JSON-LD + GeoJSON output has lots of links
the client can use to change state (sort, page, filter in different ways).



## A few things to understand first:

- Open Context uses solr dynamic fields to represent project specific attributes
(descriptive properties); projects; spatial contexts; and other metadata.
- Open Context uses "slugs" to identify entities in the database ("LinkedEntities", and
"Manifest" items) for both solr fields and the values in these solr fields.
- The dynamic Solr fields come in two main varieties, with two different purposes. The 
dynamic solr fields that have an "_fq" at the end are meant for filter queries (the "fq"
arguments in a Solr query). The dynamic solr fields that do not have an "_fq" are typically 
used to get facet counts. The dynamic solr fields that end with "_fq" take slugs as values. 
That means they are used for filter queres of entities in the database. The dynamic solr 
fields that don't have "_fq" are often used for getting facet counts. 



## Tests and demos:

An important goal of refactoring the search code is to add more confidence that Open Context search
functionality will behave as expected. Therefore, we need to add lots of rigorous unit (tests that
do NOT use the database) and regression (tests that require the database) testing. To invoke tests:

```
# Unit testing of the new search code:
pytest opencontext_py/tests/unit/searcher/new_solrsearcher/ -v

# Regression testing of the new search code:
pytest opencontext_py/tests/regression/searcher/new_solrsearcher/ -v

# Not a pytest test, but a demo over the Web query that responds with a solr-query dictionary:
http://127.0.0.1:8000/query/Turkey%7C%7CItaly?proj=24-murlo||1-domuztepe&q=dog

```


