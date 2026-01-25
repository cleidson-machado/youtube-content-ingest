pipeline {
    agent any
    
    stages {
        stage('Run') {
            steps {
                sh """
                    cat > .env << 'EOF'
YOUTUBE_API_KEY=AIzaSyCDazZkyzlFdF87ndOFOorUaB6yZFNA5jk
CONTENT_API_URL=https://api.aguide-ptbr.com.br/contents
CONTENT_API_TOKEN=my-token-super-recur-12345
SEARCH_QUERY=tipos de visto para portugal
TARGET_NEW_VIDEOS=10
MAX_PAGES_TO_SEARCH=10
MAX_RESULTS_PER_PAGE=10
ENABLE_DEDUPLICATION=true
ENABLE_ENRICHMENT=false
LOG_LEVEL=INFO
EOF
                    docker compose up
                """
            }
        }
    }
}

