/**
 * NetSuite Documentation Dashboard - Alpine.js Application
 * With Web Search Integration
 */

function dashboard() {
    return {
        // State
        activeTab: 'search',
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
        categories: [
            { id: 'SOAP', label: 'SOAP API', description: 'SOAP Web Services documentation' },
            { id: 'REST', label: 'REST API', description: 'REST Web Services documentation' },
            { id: 'GOVERNANCE', label: 'Governance', description: 'API limits and governance' },
            { id: 'PERMISSION', label: 'Permissions', description: 'Roles and permissions' },
            { id: 'RECORD', label: 'Records', description: 'Record types and entities' },
            { id: 'SEARCH', label: 'Search', description: 'Search and SuiteQL' },
            { id: 'CUSTOM', label: 'Customization', description: 'Custom records and fields' },
            { id: 'WEB', label: 'Web', description: 'Cached web search results' },
        ],

        // Initialize
        async init() {
            await Promise.all([
                this.loadStats(),
                this.checkWebSearchStatus()
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

        // Perform semantic search
        async performSearch() {
            if (!this.searchQuery.trim()) return;

            this.isSearching = true;
            this.searchResults = [];

            try {
                const payload = {
                    query: this.searchQuery,
                    top_k: 10,
                    include_web: this.includeWebSearch
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
