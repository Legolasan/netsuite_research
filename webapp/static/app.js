/**
 * Connector Research Platform - Alpine.js Application
 * Multi-connector research with per-connector Pinecone indices
 */

function dashboard() {
    return {
        // State
        activeTab: 'connectors',  // Default to connectors dashboard
        searchQuery: '',
        searchResults: [],
        isSearching: false,
        chatInput: '',
        chatMessages: [],
        isChatLoading: false,
        selectedCategory: '',
        stats: {},
        includeWebSearch: true,  // Web search toggle
        webSearchStatus: {
            available: false,
            has_tavily: false,
            has_cache: false,
            message: 'Checking...'
        },
        // PRD State
        prdSubTab: 'summary',
        prdData: {
            summary: null,
            comparison: null,
            roadmap: null,
        },
        prdLoading: false,
        prdLoaded: false,
        
        // Connector State
        connectors: [],
        connectorsLoading: false,
        connectorsLoaded: false,
        showNewConnectorModal: false,
        isCreatingConnector: false,
        newConnector: {
            name: '',
            type: 'rest_api',
            github_url: '',
            description: ''
        },
        connectorTypes: [
            { id: 'rest_api', label: 'REST API' },
            { id: 'graphql', label: 'GraphQL' },
            { id: 'soap', label: 'SOAP' },
            { id: 'jdbc', label: 'JDBC' },
            { id: 'sdk', label: 'SDK' },
            { id: 'webhook', label: 'Webhook' },
            { id: 'advertising', label: 'Ad Platform' },
            { id: 'warehouse', label: 'Warehouse' }
        ],
        
        categories: [
            { id: 'SOAP', label: 'SOAP API', description: 'SOAP Web Services documentation' },
            { id: 'REST', label: 'REST API', description: 'REST Web Services documentation' },
            { id: 'GOVERNANCE', label: 'Governance', description: 'API limits and governance' },
            { id: 'PERMISSION', label: 'Permissions', description: 'Roles and permissions' },
            { id: 'RECORD', label: 'Records', description: 'Record types and entities' },
            { id: 'SEARCH', label: 'Search', description: 'Search and SuiteQL' },
            { id: 'CUSTOM', label: 'Customization', description: 'Custom records and fields' },
            { id: 'CODE', label: 'Code', description: 'Connector Java code' },
            { id: 'CONNECTOR_OBJECTS', label: 'Connector Objects', description: 'Implemented NetSuite objects' },
            { id: 'RESEARCH', label: 'Research', description: 'Internal research documents' },
            { id: 'WEB', label: 'Web', description: 'Cached web search results' },
        ],

        // Initialize
        async init() {
            await Promise.all([
                this.loadStats(),
                this.checkWebSearchStatus(),
                this.loadConnectors()
            ]);
        },

        // Load index statistics
        async loadStats() {
            try {
                const response = await fetch('/api/stats');
                if (response.ok) {
                    this.stats = await response.json();
                } else {
                    this.stats = { status: 'disconnected', total_vectors: 0 };
                }
            } catch (error) {
                console.error('Failed to load stats:', error);
                this.stats = { status: 'error', total_vectors: 0 };
            }
        },

        // Check web search availability
        async checkWebSearchStatus() {
            try {
                const response = await fetch('/api/web-search-status');
                if (response.ok) {
                    this.webSearchStatus = await response.json();
                } else {
                    this.webSearchStatus = {
                        available: false,
                        has_tavily: false,
                        has_cache: false,
                        message: 'Web search unavailable'
                    };
                }
            } catch (error) {
                console.error('Failed to check web search status:', error);
                this.webSearchStatus = {
                    available: false,
                    has_tavily: false,
                    has_cache: false,
                    message: 'Error checking status'
                };
            }
        },

        // Load PRD data
        async loadPRDData() {
            if (this.prdLoaded) return;
            
            this.prdLoading = true;
            
            try {
                const response = await fetch('/api/prd/all');
                if (response.ok) {
                    this.prdData = await response.json();
                    this.prdLoaded = true;
                } else {
                    console.error('Failed to load PRD data');
                    this.prdData = { summary: null, comparison: null, roadmap: null };
                }
            } catch (error) {
                console.error('PRD data loading error:', error);
                this.prdData = { summary: null, comparison: null, roadmap: null };
            } finally {
                this.prdLoading = false;
            }
        },

        // =====================
        // Connector Methods
        // =====================
        
        async loadConnectors() {
            if (this.connectorsLoaded && this.connectors.length > 0) return;
            
            this.connectorsLoading = true;
            
            try {
                const response = await fetch('/api/connectors');
                if (response.ok) {
                    const data = await response.json();
                    this.connectors = data.connectors;
                    this.connectorsLoaded = true;
                } else {
                    console.error('Failed to load connectors');
                    this.connectors = [];
                }
            } catch (error) {
                console.error('Connectors loading error:', error);
                this.connectors = [];
            } finally {
                this.connectorsLoading = false;
            }
        },
        
        async createConnector() {
            if (!this.newConnector.name) return;
            
            this.isCreatingConnector = true;
            
            try {
                const response = await fetch('/api/connectors', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: this.newConnector.name,
                        connector_type: this.newConnector.type,
                        github_url: this.newConnector.github_url || null,
                        description: this.newConnector.description || ''
                    })
                });
                
                if (response.ok) {
                    const connector = await response.json();
                    this.connectors.push(connector);
                    this.showNewConnectorModal = false;
                    this.newConnector = { name: '', type: 'rest_api', github_url: '', description: '' };
                    
                    // Optionally auto-start research
                    if (confirm('Connector created! Start research generation now?')) {
                        this.startResearch(connector.id);
                    }
                } else {
                    const error = await response.json();
                    alert('Failed to create connector: ' + (error.detail || 'Unknown error'));
                }
            } catch (error) {
                console.error('Create connector error:', error);
                alert('Failed to create connector: ' + error.message);
            } finally {
                this.isCreatingConnector = false;
            }
        },
        
        async startResearch(connectorId) {
            try {
                const response = await fetch(`/api/connectors/${connectorId}/generate`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    // Update local connector status
                    const connector = this.connectors.find(c => c.id === connectorId);
                    if (connector) {
                        connector.status = 'researching';
                    }
                    
                    // Start polling for progress
                    this.pollResearchProgress(connectorId);
                } else {
                    const error = await response.json();
                    alert('Failed to start research: ' + (error.detail || 'Unknown error'));
                }
            } catch (error) {
                console.error('Start research error:', error);
                alert('Failed to start research: ' + error.message);
            }
        },
        
        async pollResearchProgress(connectorId) {
            const poll = async () => {
                try {
                    const response = await fetch(`/api/connectors/${connectorId}/status`);
                    if (response.ok) {
                        const status = await response.json();
                        
                        // Update local connector
                        const connector = this.connectors.find(c => c.id === connectorId);
                        if (connector) {
                            connector.status = status.status;
                            connector.progress = status.progress;
                        }
                        
                        // Continue polling if still running
                        if (status.is_running) {
                            setTimeout(poll, 2000);
                        } else if (status.status === 'complete') {
                            // Refresh connector data
                            this.connectorsLoaded = false;
                            await this.loadConnectors();
                        }
                    }
                } catch (error) {
                    console.error('Poll progress error:', error);
                }
            };
            
            poll();
        },
        
        async cancelResearch(connectorId) {
            if (!confirm('Are you sure you want to cancel this research?')) return;
            
            try {
                const response = await fetch(`/api/connectors/${connectorId}/cancel`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    const connector = this.connectors.find(c => c.id === connectorId);
                    if (connector) {
                        connector.status = 'cancelled';
                    }
                }
            } catch (error) {
                console.error('Cancel research error:', error);
            }
        },
        
        async deleteConnector(connectorId) {
            if (!confirm('Are you sure you want to delete this connector? This cannot be undone.')) return;
            
            try {
                const response = await fetch(`/api/connectors/${connectorId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    this.connectors = this.connectors.filter(c => c.id !== connectorId);
                } else {
                    const error = await response.json();
                    alert('Failed to delete connector: ' + (error.detail || 'Unknown error'));
                }
            } catch (error) {
                console.error('Delete connector error:', error);
                alert('Failed to delete connector: ' + error.message);
            }
        },
        
        async viewConnectorResearch(connectorId) {
            try {
                const response = await fetch(`/api/connectors/${connectorId}/research`);
                if (response.ok) {
                    const data = await response.json();
                    // Open in new tab or modal
                    const blob = new Blob([data.content], { type: 'text/markdown' });
                    const url = URL.createObjectURL(blob);
                    window.open(url, '_blank');
                }
            } catch (error) {
                console.error('View research error:', error);
                alert('Failed to load research document');
            }
        },
        
        async searchConnector(connectorId) {
            const query = prompt('Enter search query for this connector:');
            if (!query) return;
            
            this.activeTab = 'search';
            this.searchQuery = query;
            // TODO: Add connector-specific search filter
            this.performSearch();
        },

        // Perform semantic search
        async performSearch() {
            if (!this.searchQuery.trim()) return;

            this.isSearching = true;
            this.searchResults = [];

            try {
                const payload = {
                    query: this.searchQuery,
                    top_k: 5,  // Reduced since we're generating summaries
                    include_web: this.includeWebSearch,
                    include_summaries: true,  // Enable AI summaries
                    max_summaries: 5
                };

                if (this.selectedCategory) {
                    payload.category = this.selectedCategory;
                }

                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    const data = await response.json();
                    this.searchResults = data.results;
                } else {
                    const error = await response.json();
                    console.error('Search failed:', error);
                    alert('Search failed: ' + (error.detail || 'Unknown error'));
                }
            } catch (error) {
                console.error('Search error:', error);
                alert('Search failed: ' + error.message);
            } finally {
                this.isSearching = false;
            }
        },

        // Send chat message
        async sendMessage(predefinedMessage = null) {
            const message = predefinedMessage || this.chatInput.trim();
            if (!message) return;

            // Add user message
            this.chatMessages.push({
                role: 'user',
                content: message
            });

            this.chatInput = '';
            this.isChatLoading = true;

            // Scroll to bottom
            this.$nextTick(() => {
                const container = this.$refs.chatContainer;
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            });

            try {
                const payload = {
                    message: message,
                    top_k: 5,
                    include_web: this.includeWebSearch
                };

                if (this.selectedCategory) {
                    payload.category = this.selectedCategory;
                }

                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    const data = await response.json();
                    this.chatMessages.push({
                        role: 'assistant',
                        content: data.answer,
                        sources: data.sources,
                        doc_sources: data.doc_sources || [],
                        web_sources: data.web_sources || []
                    });
                } else {
                    const error = await response.json();
                    this.chatMessages.push({
                        role: 'assistant',
                        content: 'Sorry, I encountered an error: ' + (error.detail || 'Unknown error'),
                        sources: [],
                        doc_sources: [],
                        web_sources: []
                    });
                }
            } catch (error) {
                console.error('Chat error:', error);
                this.chatMessages.push({
                    role: 'assistant',
                    content: 'Sorry, I encountered an error: ' + error.message,
                    sources: [],
                    doc_sources: [],
                    web_sources: []
                });
            } finally {
                this.isChatLoading = false;

                // Scroll to bottom
                this.$nextTick(() => {
                    const container = this.$refs.chatContainer;
                    if (container) {
                        container.scrollTop = container.scrollHeight;
                    }
                });
            }
        },

        // Get category CSS class
        getCategoryClass(category) {
            const classes = {
                'SOAP': 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
                'REST': 'bg-green-500/20 text-green-400 border border-green-500/30',
                'GOVERNANCE': 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
                'PERMISSION': 'bg-red-500/20 text-red-400 border border-red-500/30',
                'RECORD': 'bg-purple-500/20 text-purple-400 border border-purple-500/30',
                'SEARCH': 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30',
                'CUSTOM': 'bg-pink-500/20 text-pink-400 border border-pink-500/30',
                'CODE': 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
                'CONNECTOR_OBJECTS': 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
                'CONNECTOR_TRANSACTIONS': 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
                'CONNECTOR_ITEMS': 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
                'RESEARCH': 'bg-teal-500/20 text-teal-400 border border-teal-500/30',
                'RESEARCH_OBJECTS': 'bg-teal-500/20 text-teal-400 border border-teal-500/30',
                'RESEARCH_REPLICATION': 'bg-teal-500/20 text-teal-400 border border-teal-500/30',
                'RESEARCH_GOVERNANCE': 'bg-teal-500/20 text-teal-400 border border-teal-500/30',
                'WEB': 'bg-green-500/20 text-green-400 border border-green-500/30',
                'GENERAL': 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
            };
            return classes[category] || classes['GENERAL'];
        },

        // Render markdown to HTML
        renderMarkdown(text) {
            if (!text) return '';
            try {
                return marked.parse(text);
            } catch (e) {
                return text.replace(/\n/g, '<br>');
            }
        }
    };
}
