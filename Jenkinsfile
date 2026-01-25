pipeline {
    agent any
    
    stages {
        stage('Run') {
            steps {
                sh """
                    cp /opt/apps/web-scraping-process/youtube-content-ingest/.env .env
                    docker compose up
                """
            }
        }
    }
}

