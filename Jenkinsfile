pipeline {
    agent any
    
    stages {
        stage('Run') {
            steps {
                withCredentials([
                    string(credentialsId: 'youtube-api-key', variable: 'YOUTUBE_API_KEY'),
                    string(credentialsId: 'content-api-token', variable: 'CONTENT_API_TOKEN')
                ]) {
                    sh """
                        cat > .env << 'EOF'
YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
CONTENT_API_URL=https://api.aguide-ptbr.com.br/contents
CONTENT_API_TOKEN=${CONTENT_API_TOKEN}
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
}

