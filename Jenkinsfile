pipeline {
    agent any
    
    // Trigger: Run twice daily at 2am and 2pm (avoid YouTube API peak hours)
    triggers {
        cron('0 2,14 * * *')
    }
    
    // Pipeline options
    options {
        // Prevent concurrent builds to avoid quota waste and API conflicts
        disableConcurrentBuilds()
        
        // Keep last 30 builds
        buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '10'))
        
        // Timeout after 30 minutes
        timeout(time: 30, unit: 'MINUTES')
        
        // Add timestamps to console output
        timestamps()
    }
    
    // Environment variables (non-sensitive defaults)
    environment {
        // Docker image name
        IMAGE_NAME = 'youtube-ingest'
        IMAGE_TAG = 'latest'
        
        // Search configuration (can be overridden)
        SEARCH_QUERY = 'tipos de visto para portugal'
        TARGET_NEW_VIDEOS = '10'
        MAX_PAGES_TO_SEARCH = '10'
        MAX_RESULTS_PER_PAGE = '10'
        ENABLE_DEDUPLICATION = 'true'
        ENABLE_ENRICHMENT = 'false'
        LOG_LEVEL = 'INFO'
    }
    
    stages {
        stage('Checkout') {
            steps {
                script {
                    echo "📦 Checking out source code..."
                    // Code already checked out by Jenkins SCM
                    // No additional checkout needed
                    echo "Working directory: ${env.WORKSPACE}"
                }
            }
        }
        
        stage('Build Docker Image') {
            when {
                anyOf {
                    // Build if code changed
                    changeset "**/*.py"
                    changeset "requirements.txt"
                    changeset "Dockerfile"
                    // Or if image doesn't exist
                    expression { 
                        return sh(
                            script: "docker images -q ${IMAGE_NAME}:${IMAGE_TAG}",
                            returnStdout: true
                        ).trim() == ''
                    }
                }
            }
            steps {
                script {
                    echo "🐳 Building Docker image..."
                    // Build from Jenkins workspace
                    sh """
                        docker build \
                            --tag ${IMAGE_NAME}:${IMAGE_TAG} \
                            --tag ${IMAGE_NAME}:build-${BUILD_NUMBER} \
                            --label "build.number=${BUILD_NUMBER}" \
                            --label "build.date=\$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
                            .
                    """
                }
            }
        }
        
        stage('Pre-flight Checks') {
            steps {
                script {
                    echo "🔍 Running pre-flight checks..."
                    
                    // Check if Docker image exists
                    sh "docker images ${IMAGE_NAME}:${IMAGE_TAG}"
                    
                    // Check if proxy-network exists
                    sh """
                        docker network inspect proxy-network > /dev/null 2>&1 || \
                        (echo '❌ Network proxy-network not found!' && exit 1)
                    """
                    
                    // Test internet connectivity
                    sh """
                        curl -f -s -o /dev/null -w '%{http_code}' https://www.googleapis.com | grep -q 200 || \
                        (echo '❌ Cannot reach Google APIs!' && exit 1)
                    """
                    
                    echo "✅ Pre-flight checks passed"
                }
            }
        }
        
        stage('Execute Pipeline') {
            steps {
                script {
                    echo "🚀 Executing YouTube content ingest pipeline..."
                    
                    // Use Jenkins credentials for sensitive data
                    withCredentials([
                        string(credentialsId: 'youtube-api-key', variable: 'YOUTUBE_API_KEY'),
                        string(credentialsId: 'content-api-token', variable: 'CONTENT_API_TOKEN'),
                        string(credentialsId: 'content-api-url', variable: 'CONTENT_API_URL')
                    ]) {
                        // Retry up to 2 times on failure (network issues, etc.)
                        retry(2) {
                            sh """
                                docker run --rm \
                                    --name youtube-ingest-${BUILD_NUMBER} \
                                    --network proxy-network \
                                    -e YOUTUBE_API_KEY="${YOUTUBE_API_KEY}" \
                                    -e CONTENT_API_URL="${CONTENT_API_URL}" \
                                    -e CONTENT_API_TOKEN="${CONTENT_API_TOKEN}" \
                                    -e SEARCH_QUERY="${SEARCH_QUERY}" \
                                    -e TARGET_NEW_VIDEOS="${TARGET_NEW_VIDEOS}" \
                                    -e MAX_PAGES_TO_SEARCH="${MAX_PAGES_TO_SEARCH}" \
                                    -e MAX_RESULTS_PER_PAGE="${MAX_RESULTS_PER_PAGE}" \
                                    -e ENABLE_DEDUPLICATION="${ENABLE_DEDUPLICATION}" \
                                    -e ENABLE_ENRICHMENT="${ENABLE_ENRICHMENT}" \
                                    -e LOG_LEVEL="${LOG_LEVEL}" \
                                    ${IMAGE_NAME}:${IMAGE_TAG} 2>&1 | tee pipeline-output.log
                            """
                        }
                    }
                }
            }
        }
        
        stage('Parse Results') {
            steps {
                script {
                    echo "📊 Parsing pipeline results..."
                    
                    // Extract metrics from logs
                    def pagesSearched = sh(
                        script: "grep 'Pages Searched:' pipeline-output.log | awk '{print \$NF}' || echo '0'",
                        returnStdout: true
                    ).trim()
                    
                    def videosFound = sh(
                        script: "grep 'New Videos Found:' pipeline-output.log | awk '{print \$NF}' || echo '0'",
                        returnStdout: true
                    ).trim()
                    
                    def videosPosted = sh(
                        script: "grep 'Videos Posted:' pipeline-output.log | awk '{print \$NF}' || echo '0'",
                        returnStdout: true
                    ).trim()
                    
                    def videosFailed = sh(
                        script: "grep 'Videos Failed:' pipeline-output.log | awk '{print \$NF}' || echo '0'",
                        returnStdout: true
                    ).trim()
                    
                    // Store as build description
                    currentBuild.description = "Pages: ${pagesSearched} | Found: ${videosFound} | Posted: ${videosPosted} | Failed: ${videosFailed}"
                    
                    echo """
                    ╔════════════════════════════════════════╗
                    ║       PIPELINE EXECUTION SUMMARY       ║
                    ╠════════════════════════════════════════╣
                    ║  Pages Searched:      ${pagesSearched.padRight(14)}║
                    ║  Videos Found:        ${videosFound.padRight(14)}║
                    ║  Videos Posted:       ${videosPosted.padRight(14)}║
                    ║  Videos Failed:       ${videosFailed.padRight(14)}║
                    ╚════════════════════════════════════════╝
                    """
                    
                    // Archive logs
                    archiveArtifacts artifacts: 'pipeline-output.log', fingerprint: true
                }
            }
        }
    }
    
    post {
        always {
            script {
                echo "🧹 Cleaning up..."
                
                // Remove old containers (if any stuck)
                sh """
                    docker ps -a --filter "name=youtube-ingest-" --format "{{.ID}}" | \
                    xargs -r docker rm -f || true
                """
                
                // Clean up old images (keep last 5 builds)
                sh """
                    docker images ${IMAGE_NAME} --format "{{.Tag}}" | \
                    grep "build-" | \
                    sort -t'-' -k2 -rn | \
                    tail -n +6 | \
                    xargs -r -I {} docker rmi ${IMAGE_NAME}:{} || true
                """
                
                // Prune unused Docker resources (older than 24h)
                sh "docker system prune -f --filter 'until=24h' || true"
            }
        }
        
        success {
            script {
                echo "✅ Pipeline executed successfully!"
                
                // Optional: Send success notification
                // emailext (
                //     subject: "✅ YouTube Ingest Success - Build #${BUILD_NUMBER}",
                //     body: """
                //         Pipeline executed successfully!
                //         
                //         Build: ${BUILD_URL}
                //         ${currentBuild.description}
                //         
                //         See attached logs for details.
                //     """,
                //     to: "devops@aguide-ptbr.com.br",
                //     attachLog: true
                // )
            }
        }
        
        failure {
            script {
                echo "❌ Pipeline execution failed!"
                
                // Optional: Send failure notification
                // emailext (
                //     subject: "❌ YouTube Ingest Failed - Build #${BUILD_NUMBER}",
                //     body: """
                //         Pipeline execution failed!
                //         
                //         Build: ${BUILD_URL}console
                //         
                //         Please check the console output for details.
                //     """,
                //     to: "devops@aguide-ptbr.com.br",
                //     attachLog: true
                // )
            }
        }
        
        unstable {
            script {
                echo "⚠️ Pipeline execution unstable!"
            }
        }
    }
}
