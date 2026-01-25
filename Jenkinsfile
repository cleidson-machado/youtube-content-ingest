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
                    
                    // Extract metrics from summary section
                    def pagesSearched = sh(
                        script: "grep 'Pages Searched:' pipeline-output.log | tail -1 | awk -F': ' '{print \$2}' || echo '0'",
                        returnStdout: true
                    ).trim()
                    
                    def videosFound = sh(
                        script: "grep 'New Videos Found:' pipeline-output.log | tail -1 | awk -F': ' '{print \$2}' || echo '0'",
                        returnStdout: true
                    ).trim()
                    
                    def videosPosted = sh(
                        script: "grep 'Videos Posted:' pipeline-output.log | tail -1 | awk -F': ' '{print \$2}' || echo '0'",
                        returnStdout: true
                    ).trim()
                    
                    def videosFailed = sh(
                        script: "grep 'Videos Failed:' pipeline-output.log | tail -1 | awk -F': ' '{print \$2}' || echo '0'",
                        returnStdout: true
                    ).trim()
                    
                    // Set build description
                    currentBuild.description = "Found: ${videosFound} | Posted: ${videosPosted} | Failed: ${videosFailed}"
                    
                    echo """
                    ════════════════════════════════════════
                         PIPELINE EXECUTION SUMMARY
                    ════════════════════════════════════════
                    Pages Searched:    ${pagesSearched}
                    New Videos Found:  ${videosFound}
                    Videos Posted:     ${videosPosted}
                    Videos Failed:     ${videosFailed}
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

