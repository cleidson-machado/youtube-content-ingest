pipeline {
    agent any
    
    // Trigger: Run twice daily at 2am and 2pm
    triggers {
        cron('0 2,14 * * *')
    }
    
    options {
        // Prevent concurrent builds
        disableConcurrentBuilds()
        
        // Keep last 30 builds
        buildDiscarder(logRotator(numToKeepStr: '30'))
        
        // Timeout after 30 minutes
        timeout(time: 30, unit: 'MINUTES')
        
        // Timestamps in console
        timestamps()
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo "📦 Code checked out to: ${env.WORKSPACE}"
            }
        }
        
        stage('Run Pipeline') {
            steps {
                script {
                    echo "🚀 Executing YouTube Ingest via docker-compose..."
                    
                    // Run docker-compose and capture output
                    sh """
                        cd ${env.WORKSPACE}
                        docker-compose up --abort-on-container-exit 2>&1 | tee pipeline-output.log
                    """
                }
            }
        }
        
        stage('Parse Results') {
            steps {
                script {
                    echo "📊 Parsing pipeline results..."
                    
                    // Extract metrics from logs (if available)
                    def videosFound = sh(
                        script: "grep -i 'videos found\\|new videos' pipeline-output.log | tail -1 || echo 'N/A'",
                        returnStdout: true
                    ).trim()
                    
                    def videosPosted = sh(
                        script: "grep -i 'videos posted\\|posted successfully' pipeline-output.log | tail -1 || echo 'N/A'",
                        returnStdout: true
                    ).trim()
                    
                    echo """
                    ════════════════════════════════════════
                         PIPELINE EXECUTION SUMMARY
                    ════════════════════════════════════════
                    Videos Found:  ${videosFound}
                    Videos Posted: ${videosPosted}
                    ════════════════════════════════════════
                    """
                    
                    // Archive logs
                    archiveArtifacts artifacts: 'pipeline-output.log', allowEmptyArchive: true
                }
            }
        }
    }
    
    post {
        always {
            script {
                echo "🧹 Cleaning up containers..."
                sh """
                    docker-compose down || true
                    docker system prune -f --filter 'until=24h' || true
                """
            }
        }
        
        success {
            echo "✅ Pipeline executed successfully!"
        }
        
        failure {
            echo "❌ Pipeline execution failed!"
        }
    }
}

