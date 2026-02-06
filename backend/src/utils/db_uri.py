from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

def normalize_db_uri_for_pgvector(db_uri: str) -> str:
    parsed = urlparse(db_uri)
    scheme = "postgresql" if parsed.scheme in ("postgresql", "postgres", "postgresql+psycopg", "postgresql+asyncpg") else parsed.scheme
    query_params = parse_qs(parsed.query)
    filtered = {k: v for k, v in query_params.items() if k not in ("sslmode",)}
    new_query = urlencode(filtered, doseq=True) if filtered else ""
    return urlunparse((scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
