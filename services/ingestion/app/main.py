import functions_framework

app = functions_framework.create_app(target="ingest", source="app/live.py")
