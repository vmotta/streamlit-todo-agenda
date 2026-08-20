#!/bin/sh
set -eu

alembic upgrade head
exec streamlit run streamlit_app.py --server.address=0.0.0.0 --server.port=8501

