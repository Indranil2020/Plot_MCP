import React, { useState, useEffect } from 'react';
import './GalleryBrowser.css';
import thumbnails from '../gallery_thumbnails.json';

const GalleryBrowser = ({ onSelectExample, onClose }) => {
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);
    const [activeExample, setActiveExample] = useState(null); // Added activeExample state

    useEffect(() => {
        // Load gallery knowledge base
        fetch('/backend/matplotlib_gallery_kb.json')
            .then(res => res.json())
            .then(data => {
                const cats = Object.entries(data.categories || {}).map(([name, info]) => ({
                    name,
                    count: info.count,
                    examples: info.examples || []
                }));
                setCategories(cats.sort((a, b) => b.count - a.count));
                setLoading(false);
            })
            .catch(err => {
                console.error('Error loading gallery:', err);
                setLoading(false);
            });
    }, []);

    const filteredCategories = categories.filter(cat => {
        // Search in category name
        if (cat.name.toLowerCase().includes(searchQuery.toLowerCase())) {
            return true;
        }
        // Search in example titles within the category
        return cat.examples.some(ex =>
            ex.title.toLowerCase().includes(searchQuery.toLowerCase())
        );
    }).map(cat => {
        // If searching, also filter examples within each category
        if (searchQuery) {
            return {
                ...cat,
                examples: cat.examples.filter(ex =>
                    ex.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    cat.name.toLowerCase().includes(searchQuery.toLowerCase())
                )
            };
        }
        return cat;
    });

    const handleCategoryClick = (category) => {
        setSelectedCategory(selectedCategory === category.name ? null : category.name);
    };

    const handleExampleClick = (example) => {
        onSelectExample({
            title: example.title,
            filename: example.filename,
            category: selectedCategory
        });
    };

    if (loading) {
        return (
            <div className="gallery-browser">
                <div className="gallery-header">
                    <h2>📚 Gallery Browser</h2>
                    <button onClick={onClose} className="close-btn">✕</button>
                </div>
                <div className="loading">Loading gallery...</div>
            </div>
        );
    }

    return (
        <div className="gallery-browser">
            {/* Header */}
            <div className="gallery-header">
                <div>
                    <h2>📚 Gallery Browser</h2>
                    <p className="gallery-subtitle">509 Official Examples</p>
                </div>
                <button onClick={onClose} className="close-btn">✕</button>
            </div>

            {/* Search */}
            <div className="gallery-search">
                <input
                    type="text"
                    placeholder="Search categories..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="search-input"
                />
            </div>

            {/* Categories */}
            <div className="gallery-content">
                {filteredCategories.map(category => (
                    <div key={category.name} className="category-section">
                        <div
                            className="category-header"
                            onClick={() => handleCategoryClick(category)}
                        >
                            <div className="category-title">
                                <span className="category-icon">
                                    {selectedCategory === category.name ? '▼' : '▶'}
                                </span>
                                <span className="category-name">
                                    {category.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </span>
                            </div>
                            <span className="category-count">{category.count}</span>
                        </div>

                        {selectedCategory === category.name && (
                            <div className="examples-list">
                                {category.examples.map((example, idx) => (
                                    <div
                                        key={idx}
                                        className="example-item"
                                        onClick={() => handleExampleClick(example)}
                                    >
                                        <div className="example-thumbnail">
                                            {thumbnails[example.title] ? (
                                                <img
                                                    src={thumbnails[example.title]}
                                                    alt={example.title}
                                                    loading="lazy"
                                                />
                                            ) : (
                                                <span className="example-icon">[PLOT]</span>
                                            )}
                                        </div>
                                        <span className="example-title">{example.title}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Footer */}
            <div className="gallery-footer">
                <p>Click any example to apply it to your data</p>
            </div>
        </div>
    );
};

export default GalleryBrowser;
