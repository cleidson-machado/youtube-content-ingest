pipeline {
    agent any
    
    stages {
        stage('Run') {
            steps {
                withCredentials([
                    string(credentialsId: 'youtube-api-key', variable: 'YOUTUBE_API_KEY'),
                    string(credentialsId: 'content-api-email', variable: 'CONTENT_API_EMAIL'),
                    string(credentialsId: 'content-api-password', variable: 'CONTENT_API_PASSWORD')
                ]) {
                    sh """
                        # Clean up any existing containers
                        docker compose down || true
                        docker rm -f youtube-ingest || true
                        
                        # Run with environment variables (no .env needed!)
                        YOUTUBE_API_KEY='${YOUTUBE_API_KEY}' \
                        CONTENT_API_EMAIL='${CONTENT_API_EMAIL}' \
                        CONTENT_API_PASSWORD='${CONTENT_API_PASSWORD}' \
                        docker compose up --build --abort-on-container-exit
                    """
                }
            }
        }
    }
    
    post {
        always {
            sh "docker compose down || true"
        }
    }
}

