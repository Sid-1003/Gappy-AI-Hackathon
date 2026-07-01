document.addEventListener('DOMContentLoaded', () => {
    // State Management
    let allItems = [];
    let selectedStudioItemIds = [];
    let selectedTransformFormat = 'task_list';
    let currentDetailItem = null;
    
    // DOM Elements
    const navButtons = document.querySelectorAll('.nav-menu .nav-btn');
    const tabs = document.querySelectorAll('.workspace-tab');
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const searchPills = document.querySelectorAll('.pill');
    const aiBanner = document.getElementById('aiSynthesisBanner');
    const aiSynthesisText = document.getElementById('aiSynthesisText');
    const closeBannerBtn = document.getElementById('closeBannerBtn');
    
    // Modal Elements (Add/Edit)
    const itemModal = document.getElementById('itemModal');
    const openAddModalBtn = document.getElementById('openAddModalBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const cancelModalBtn = document.getElementById('cancelModalBtn');
    const itemForm = document.getElementById('itemForm');
    
    // Detail Modal Elements (Read / Reader View)
    const detailModal = document.getElementById('detailModal');
    const closeDetailModalBtn = document.getElementById('closeDetailModalBtn');
    const closeDetailBtn = document.getElementById('closeDetailBtn');
    const deleteDetailBtn = document.getElementById('deleteDetailBtn');
    
    // Combined Modal Elements
    const runSecondBrainBtn = document.getElementById('runSecondBrainBtn');
    const combineModal = document.getElementById('combineModal');
    const closeCombineModalBtn = document.getElementById('closeCombineModalBtn');
    const closeCombineBtn = document.getElementById('closeCombineBtn');
    const combinedNotesClusters = document.getElementById('combinedNotesClusters');
    
    // Studio Elements
    const studioSelectionList = document.getElementById('studioSelectionList');
    const actionOptBtns = document.querySelectorAll('.action-opt-btn');
    const generateActionBtn = document.getElementById('generateActionBtn');
    const actionOutputText = document.getElementById('actionOutputText');
    const copyDocBtn = document.getElementById('copyDocBtn');
    
    // Filter Elements
    const filterType = document.getElementById('filterType');
    const filterCategory = document.getElementById('filterCategory');
    const mobileToggle = document.getElementById('mobileToggle');
    const sidebar = document.getElementById('sidebar');

    // 1. System Status Check
    fetchSystemStatus();
    loadDashboardData();

    // Navigation Tab Handler
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            navButtons.forEach(b => b.classList.remove('active'));
            tabs.forEach(t => t.classList.remove('active'));
            
            btn.classList.add('active');
            const targetTab = document.getElementById(`tab-${btn.dataset.tab}`);
            if (targetTab) targetTab.classList.add('active');
            
            if (btn.dataset.tab === 'graph') {
                renderKnowledgeGraph();
            } else if (btn.dataset.tab === 'action-center') {
                renderStudioSelectionList();
            }
        });
    });

    // Mobile Sidebar Toggle
    if (mobileToggle) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }

    // 2. Fetch System Status
    async function fetchSystemStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            document.getElementById('dbEngineLabel').textContent = `DB: ${data.database_engine}`;
        } catch (e) {
            document.getElementById('dbEngineLabel').textContent = `DB: Local Storage`;
        }
    }

    // 3. Load Main Data
    async function loadDashboardData() {
        try {
            const res = await fetch('/api/items');
            allItems = await res.json();
            
            updateMetrics(allItems);
            renderRecentItems(allItems);
            renderVaultItems(allItems);
            fetchInsights();
        } catch (err) {
            console.error('Failed to load items:', err);
        }
    }

    // Update Dashboard Metrics
    function updateMetrics(items) {
        document.getElementById('statTotalItems').textContent = items.length;
        
        const deadlines = items.filter(i => i.deadline || i.priority === 'Urgent' || i.priority === 'High');
        document.getElementById('statDeadlines').textContent = deadlines.length;
        
        const ideas = items.filter(i => i.type === 'idea');
        document.getElementById('statIdeas').textContent = ideas.length;
        
        const links = items.filter(i => i.type === 'link' || i.url);
        document.getElementById('statLinks').textContent = links.length;
    }

    // Render Recent Items
    function renderRecentItems(items) {
        const grid = document.getElementById('recentItemsGrid');
        grid.innerHTML = '';
        
        const recent = items.slice(0, 6);
        if (recent.length === 0) {
            grid.innerHTML = '<div class="glass" style="padding:20px; grid-column:1/-1;">No items captured yet. Click "+ Capture Knowledge" to start!</div>';
            return;
        }
        
        recent.forEach(item => {
            grid.appendChild(createItemCard(item));
        });
    }

    // Render Vault Items with Filters
    function renderVaultItems(items) {
        const grid = document.getElementById('vaultItemsGrid');
        grid.innerHTML = '';
        
        let filtered = items;
        const selectedType = filterType ? filterType.value : 'all';
        const selectedCat = filterCategory ? filterCategory.value : 'all';
        
        if (selectedType !== 'all') {
            filtered = filtered.filter(i => i.type.toLowerCase() === selectedType.toLowerCase());
        }
        if (selectedCat !== 'all') {
            filtered = filtered.filter(i => i.category.toLowerCase() === selectedCat.toLowerCase());
        }
        
        if (filtered.length === 0) {
            grid.innerHTML = '<div class="glass" style="padding:20px; grid-column:1/-1;">No matching items found in Vault.</div>';
            return;
        }
        
        filtered.forEach(item => {
            grid.appendChild(createItemCard(item));
        });
    }

    // Filter Change Listeners
    if (filterType) filterType.addEventListener('change', () => renderVaultItems(allItems));
    if (filterCategory) filterCategory.addEventListener('change', () => renderVaultItems(allItems));

    // Create Item Card HTML Element (Interactive & Clickable)
    function createItemCard(item) {
        const card = document.createElement('div');
        card.className = 'item-card glass';
        
        const deadlineHTML = item.deadline ? `<span class="deadline-pill">⏰ ${escapeHTML(item.deadline)}</span>` : '';
        const actionsHTML = (item.extracted_actions && item.extracted_actions !== 'No explicit action items detected.')
            ? `<div class="item-actions-box"><strong>Extracted Actions:</strong><br>${escapeHTML(item.extracted_actions).replace(/\n/g, '<br>')}</div>`
            : '';
            
        card.innerHTML = `
            <div>
                <div class="item-card-header">
                    <span class="item-type-badge type-${item.type}">${item.type}</span>
                    ${deadlineHTML}
                </div>
                <h3 class="item-title">${escapeHTML(item.title)}</h3>
                <p class="item-content">${escapeHTML(item.content)}</p>
                <span class="click-to-read-hint">📖 Click note to read full text →</span>
                ${actionsHTML}
            </div>
            <div class="item-meta">
                <span>🏷️ ${escapeHTML(item.category)}</span>
                <button class="btn-link delete-btn" data-id="${item.id}">Delete</button>
            </div>
        `;
        
        // Open detail reader on card click
        card.addEventListener('click', (e) => {
            if (e.target.classList.contains('delete-btn')) return;
            openDetailModal(item);
        });
        
        card.querySelector('.delete-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteItem(item.id);
        });
        
        return card;
    }

    // Open Detail View Reader Modal
    function openDetailModal(item) {
        currentDetailItem = item;
        
        document.getElementById('detailTitle').textContent = item.title;
        const badge = document.getElementById('detailBadge');
        badge.textContent = item.type.toUpperCase();
        badge.className = `item-type-badge type-${item.type}`;
        
        // Render metadata chips
        const metaRow = document.getElementById('detailMetaRow');
        metaRow.innerHTML = `
            <span class="meta-chip">📁 Category: ${escapeHTML(item.category)}</span>
            <span class="meta-chip">🔥 Priority: ${escapeHTML(item.priority || 'Medium')}</span>
            ${item.deadline ? `<span class="meta-chip" style="color:#f87171; border-color:rgba(239, 68, 68, 0.4);">⏰ Deadline: ${escapeHTML(item.deadline)}</span>` : ''}
            ${item.url ? `<span class="meta-chip"><a href="${escapeHTML(item.url)}" target="_blank" style="color:var(--accent); text-decoration:none;">🔗 Visit Link ↗</a></span>` : ''}
        `;
        
        // Render AI Summary if present
        const summarySec = document.getElementById('detailSummarySection');
        if (item.ai_summary) {
            document.getElementById('detailAiSummary').textContent = item.ai_summary;
            summarySec.style.display = 'block';
        } else {
            summarySec.style.display = 'none';
        }
        
        // Render Full Un-truncated Content
        document.getElementById('detailFullContent').textContent = item.content;
        
        // Render Extracted Actions
        const actionsSec = document.getElementById('detailActionsSection');
        if (item.extracted_actions && item.extracted_actions !== 'No explicit action items detected.') {
            document.getElementById('detailExtractedActions').textContent = item.extracted_actions;
            actionsSec.style.display = 'block';
        } else {
            actionsSec.style.display = 'none';
        }
        
        detailModal.classList.remove('hidden');
    }

    closeDetailModalBtn.addEventListener('click', () => detailModal.classList.add('hidden'));
    closeDetailBtn.addEventListener('click', () => detailModal.classList.add('hidden'));
    deleteDetailBtn.addEventListener('click', () => {
        if (currentDetailItem) {
            deleteItem(currentDetailItem.id);
            detailModal.classList.add('hidden');
        }
    });

    // 6. Run AI Second Brain - Combined Notes Logic
    if (runSecondBrainBtn) {
        runSecondBrainBtn.addEventListener('click', () => {
            combinedNotesClusters.innerHTML = '';
            
            if (allItems.length === 0) {
                combinedNotesClusters.innerHTML = '<p style="color: var(--text-muted);">No notes available in the vault to group.</p>';
                combineModal.classList.remove('hidden');
                return;
            }

            // Map to store grouped items
            const clustersMap = {};

            allItems.forEach(item => {
                const tags = item.tags ? item.tags.split(',').map(t => t.trim().toLowerCase()).filter(t => t.length > 0) : [];
                if (item.category && item.category.toLowerCase() !== 'general') {
                    tags.push(item.category.trim().toLowerCase());
                }

                tags.forEach(tag => {
                    if (!clustersMap[tag]) {
                        clustersMap[tag] = [];
                    }
                    if (!clustersMap[tag].find(i => i.id === item.id)) {
                        clustersMap[tag].push(item);
                    }
                });
            });

            // Filter clusters that have at least 2 items
            const validClusters = Object.keys(clustersMap)
                .filter(tag => clustersMap[tag].length >= 2)
                .map(tag => ({
                    topic: tag.charAt(0).toUpperCase() + tag.slice(1),
                    items: clustersMap[tag]
                }));

            if (validClusters.length === 0) {
                combinedNotesClusters.innerHTML = `
                    <div style="background: rgba(0,0,0,0.02); border: 1px dashed var(--border-glass); padding: 24px; border-radius: var(--radius-md); text-align: center;">
                        <h4 style="margin-bottom: 8px; color: var(--text-main);">No Multi-Note Clusters Found Yet</h4>
                        <p style="color: var(--text-muted); font-size: 13px; line-height: 1.5;">
                            Create some notes with overlapping tags (e.g. "hackathon", "database", or "ai") or the same category to see them automatically connected and synthesized as combined readables!
                        </p>
                    </div>
                `;
            } else {
                validClusters.forEach(async (cluster) => {
                    const clusterCard = document.createElement('div');
                    clusterCard.style.cssText = 'background: #ffffff; border: 1px solid var(--border-glass); border-radius: var(--radius-md); padding: 18px; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);';
                    
                    const titlesList = cluster.items.map(item => `<li style="margin-left: 18px; color: var(--text-muted); font-size: 13px;">${escapeHTML(item.title)}</li>`).join('');
                    
                    clusterCard.innerHTML = `
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                            <h3 style="font-size: 15.5px; color: var(--text-main); font-weight: 600;">✨ Connection Topic: "${escapeHTML(cluster.topic)}"</h3>
                            <span class="item-type-badge type-note" style="font-size: 10px; background:#f3f4f6; color:#4b5563;">${cluster.items.length} Linked Notes</span>
                        </div>
                        <div style="margin-bottom: 14px;">
                            <span style="font-size: 12px; color: var(--text-muted); font-weight: 500;">Linked Source Notes:</span>
                            <ul style="margin-top: 4px;">${titlesList}</ul>
                        </div>
                        <div style="font-size: 13.5px; color: var(--text-muted); margin-bottom: 8px; font-weight: 500;">🤖 Consolidated AI Summary:</div>
                        <div class="full-content-box summary-box" style="max-height: 250px; font-size: 13.5px; background: #faf8f5; line-height: 1.6; border: 1px solid rgba(0,0,0,0.06); padding:14px; border-radius:8px; color:var(--text-main);">🧠 Merging similar notes and generating single AI summary...</div>
                    `;
                    combinedNotesClusters.appendChild(clusterCard);

                    // Call backend to merge summarize
                    try {
                        const mergeRes = await fetch('/api/ai/merge', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ item_ids: cluster.items.map(i => i.id), target_format: 'summary' })
                        });
                        const mergeData = await mergeRes.json();
                        clusterCard.querySelector('.summary-box').innerHTML = escapeHTML(mergeData.merged_summary).replace(/\n/g, '<br>');
                    } catch (e) {
                        clusterCard.querySelector('.summary-box').textContent = 'Failed to generate merged summary.';
                    }
                });
            }

            combineModal.classList.remove('hidden');
        });

        closeCombineModalBtn.addEventListener('click', () => combineModal.classList.add('hidden'));
        closeCombineBtn.addEventListener('click', () => combineModal.classList.add('hidden'));
    }

    // Fetch AI Insights
    async function fetchInsights() {
        try {
            const res = await fetch('/api/insights');
            const insights = await res.json();
            const grid = document.getElementById('insightsGrid');
            grid.innerHTML = '';
            
            insights.forEach(ins => {
                const card = document.createElement('div');
                card.className = 'insight-card glass';
                card.innerHTML = `
                    <h4>${escapeHTML(ins.title)}</h4>
                    <p>${escapeHTML(ins.description)}</p>
                `;
                grid.appendChild(card);
            });
        } catch (e) {
            console.error('Failed to fetch insights:', e);
        }
    }

    // 4. AI Smart Search Execution
    async function executeSearch(queryStr) {
        if (!queryStr) return;
        
        try {
            const res = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: queryStr })
            });
            const data = await res.json();
            
            // Display AI Synthesis Banner
            aiSynthesisText.textContent = data.ai_synthesis;
            aiBanner.classList.remove('hidden');
            
            // Display matching items in vault and switch tab
            renderVaultItems(data.items);
            document.querySelector('[data-tab="vault"]').click();
        } catch (e) {
            console.error('Search failed:', e);
        }
    }

    searchBtn.addEventListener('click', () => executeSearch(searchInput.value));
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') executeSearch(searchInput.value);
    });

    searchPills.forEach(pill => {
        pill.addEventListener('click', () => {
            const q = pill.dataset.query;
            searchInput.value = q;
            executeSearch(q);
        });
    });

    closeBannerBtn.addEventListener('click', () => aiBanner.classList.add('hidden'));

    // 5. Modal & Item Creation
    openAddModalBtn.addEventListener('click', () => {
        document.getElementById('itemForm').reset();
        document.getElementById('itemId').value = '';
        document.getElementById('modalTitle').textContent = '✨ Capture Knowledge';
        itemModal.classList.remove('hidden');
    });

    closeModalBtn.addEventListener('click', () => itemModal.classList.add('hidden'));
    cancelModalBtn.addEventListener('click', () => itemModal.classList.add('hidden'));

    itemForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const payload = {
            title: document.getElementById('inputTitle').value,
            type: document.getElementById('inputType').value,
            category: document.getElementById('inputCategory').value || 'General',
            url: document.getElementById('inputUrl').value,
            content: document.getElementById('inputContent').value,
            deadline: document.getElementById('inputDeadline').value,
            priority: document.getElementById('inputPriority').value,
            tags: document.getElementById('inputTags').value
        };
        
        try {
            const res = await fetch('/api/items', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                itemModal.classList.add('hidden');
                loadDashboardData();
            }
        } catch (err) {
            alert('Failed to save item');
        }
    });

    async function deleteItem(id) {
        if (!confirm('Are you sure you want to delete this item?')) return;
        try {
            await fetch(`/api/items/${id}`, { method: 'DELETE' });
            loadDashboardData();
        } catch (e) {
            alert('Delete failed');
        }
    }

    // 6. Action Studio Selection & Transformation
    function renderStudioSelectionList() {
        studioSelectionList.innerHTML = '';
        if (allItems.length === 0) {
            studioSelectionList.innerHTML = '<div style="font-size:13px; color:var(--text-muted)">No items captured yet.</div>';
            return;
        }
        
        allItems.forEach(item => {
            const row = document.createElement('label');
            row.className = 'select-item-row';
            const isChecked = selectedStudioItemIds.includes(item.id);
            row.innerHTML = `
                <input type="checkbox" value="${item.id}" ${isChecked ? 'checked' : ''}>
                <span>${escapeHTML(item.title)} (${item.type})</span>
            `;
            row.querySelector('input').addEventListener('change', (e) => {
                if (e.target.checked) {
                    if (!selectedStudioItemIds.includes(item.id)) selectedStudioItemIds.push(item.id);
                } else {
                    selectedStudioItemIds = selectedStudioItemIds.filter(id => id !== item.id);
                }
            });
            studioSelectionList.appendChild(row);
        });
    }

    actionOptBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            actionOptBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedTransformFormat = btn.dataset.format;
        });
    });

    generateActionBtn.addEventListener('click', async () => {
        if (selectedStudioItemIds.length === 0) {
            alert('Please select at least one knowledge item from step 1.');
            return;
        }
        
        actionOutputText.textContent = '🧠 AI Studio synthesizing document...';
        try {
            const res = await fetch('/api/ai/transform', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    item_ids: selectedStudioItemIds,
                    target_format: selectedTransformFormat
                })
            });
            const data = await res.json();
            actionOutputText.textContent = data.document;
        } catch (e) {
            actionOutputText.textContent = 'Transformation failed.';
        }
    });

    copyDocBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(actionOutputText.textContent);
        alert('Copied to clipboard!');
    });

    // 7. Interactive Knowledge Graph Canvas Animation
    async function renderKnowledgeGraph() {
        const canvas = document.getElementById('graphCanvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
        
        try {
            const res = await fetch('/api/graph');
            const graphData = await res.json();
            
            if (graphData.nodes.length === 0) return;
            
            // Random initial node positions
            const nodes = graphData.nodes.map(n => ({
                ...n,
                x: Math.random() * (canvas.width - 200) + 100,
                y: Math.random() * (canvas.height - 200) + 100,
                vx: 0,
                vy: 0
            }));
            
            let hoveredNode = null;
            
            function animate() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                // Draw links
                ctx.strokeStyle = 'rgba(75, 85, 99, 0.2)';
                ctx.lineWidth = 1.5;
                graphData.links.forEach(link => {
                    const sourceNode = nodes.find(n => n.id === link.source);
                    const targetNode = nodes.find(n => n.id === link.target);
                    if (sourceNode && targetNode) {
                        ctx.beginPath();
                        ctx.moveTo(sourceNode.x, sourceNode.y);
                        ctx.lineTo(targetNode.x, targetNode.y);
                        ctx.stroke();
                    }
                });
                
                // Draw nodes
                nodes.forEach(node => {
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, 14, 0, Math.PI * 2);
                    
                    if (node.type === 'note') ctx.fillStyle = '#1f2937';
                    else if (node.type === 'idea') ctx.fillStyle = '#d97706';
                    else if (node.type === 'link') ctx.fillStyle = '#4b5563';
                    else ctx.fillStyle = '#dc2626';
                    
                    ctx.fill();
                    ctx.strokeStyle = '#ffffff';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                    
                    // Node Label - interactive title display
                    ctx.fillStyle = '#1f2937';
                    ctx.font = node === hoveredNode ? 'bold 13px Inter' : '12px Inter';
                    const text = node === hoveredNode ? node.label : (node.label.substring(0, 15) + '...');
                    
                    if (node === hoveredNode) {
                        ctx.save();
                        ctx.shadowColor = 'rgba(0,0,0,0.1)';
                        ctx.shadowBlur = 8;
                        ctx.fillStyle = '#ffffff';
                        ctx.strokeStyle = '#e5e7eb';
                        ctx.lineWidth = 1;
                        
                        const textWidth = ctx.measureText(text).width;
                        ctx.beginPath();
                        ctx.roundRect(node.x + 18, node.y - 12, textWidth + 16, 24, 6);
                        ctx.fill();
                        ctx.stroke();
                        ctx.restore();
                        
                        ctx.fillStyle = '#1f2937';
                        ctx.fillText(text, node.x + 26, node.y + 4);
                    } else {
                        ctx.fillText(text, node.x + 18, node.y + 4);
                    }
                });
            }

            // Mouse interaction handlers
            canvas.addEventListener('mousemove', (e) => {
                const rect = canvas.getBoundingClientRect();
                const mx = e.clientX - rect.left;
                const my = e.clientY - rect.top;
                
                hoveredNode = null;
                for (let node of nodes) {
                    const dist = Math.hypot(node.x - mx, node.y - my);
                    if (dist < 14) {
                        hoveredNode = node;
                        break;
                    }
                }
                
                canvas.style.cursor = hoveredNode ? 'pointer' : 'default';
                animate();
            });

            canvas.addEventListener('click', (e) => {
                const rect = canvas.getBoundingClientRect();
                const mx = e.clientX - rect.left;
                const my = e.clientY - rect.top;
                
                for (let node of nodes) {
                    const dist = Math.hypot(node.x - mx, node.y - my);
                    if (dist < 14) {
                        const fullItem = allItems.find(i => i.id === node.id);
                        if (fullItem) {
                            openDetailModal(fullItem);
                        }
                        break;
                    }
                }
            });
            
            animate();
        } catch (e) {
            console.error('Graph render error:', e);
        }
    }

    function escapeHTML(str) {
        if (!str) return '';
        return str.replace(/[&<>'"]/g, 
            tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
        );
    }
});
