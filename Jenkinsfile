pipeline {
    agent any
    
    stages {
        stage('Run') {
            steps {
                script {
                    // Try to use credentials if available, fallback to defaults
                    def youtubeKey = ''
                    def apiToken = ''
                    
                    try {
                        withCredentials([
                            string(credentialsId: 'youtube-api-key', variable: 'YOUTUBE_API_KEY'),
                            string(credentialsId: 'content-api-token', variable: 'CONTENT_API_TOKEN')
                        ]) {
                            youtubeKey = env.YOUTUBE_API_KEY
                            apiToken = env.CONTENT_API_TOKEN
                        }
                    } catch (Exception e) {
                        echo "⚠️  Credentials not found in Jenkins, using defaults from code"
                        youtubeKey = 'AIzaSyCDazZkyzlFdF87ndOFOorUaB6yZFNA5jk'
                        apiToken = 'my-token-super-recur-12345'
                    }
                    
                    sh """
                        cat > .env << 'EOF'
YOUTUBE_API_KEY=${youtubeKey}
CONTENT_API_URL=https://api.aguide-ptbr.com.br/contents
CONTENT_API_TOKEN=${apiToken}
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

