pipeline {
    agent any
    
    triggers {
        cron('0 2,14 * * *')
    }
    
    options {
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
    }
    
    stages {
        stage('Run') {
            steps {
                sh """
                    cd ${env.WORKSPACE}
                    docker compose down || true
                    docker rm -f youtube-ingest || true
                    docker compose up --abort-on-container-exit
                """
            }
        }
    }
    
    post {
        always {
            sh "docker compose down || true"
        }
    }
}

