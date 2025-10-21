import wikipedia
import random
import json
import os
from faker import Faker
from datetime import datetime

# Set up Wikipedia to avoid rate limiting
wikipedia.set_rate_limiting(True)
fake = Faker()

def create_data_folder():
    """Create data folder if it doesn't exist"""
    if not os.path.exists('data'):
        os.makedirs('data')
    return 'data'

def get_wikipedia_articles(max_docs=100):
    """Get Wikipedia articles with better error handling and more topics"""
    documents = []
    used_titles = set()
    
    # Expanded AI/ML topics list
    ai_ml_topics = [
        # Core AI/ML Concepts
        "Artificial Intelligence", "Machine Learning", "Deep Learning", 
        "Neural Networks", "Natural Language Processing", "Computer Vision",
        "Reinforcement Learning", "Supervised Learning", "Unsupervised Learning",
        "Semi-supervised Learning", "Transfer Learning", "Meta Learning",
        
        # Algorithms & Models
        "Random Forest", "Support Vector Machine", "Gradient Boosting",
        "K-means Clustering", "Principal Component Analysis", "Linear Regression",
        "Logistic Regression", "Decision Tree", "Naive Bayes", "K-nearest neighbors",
        "Convolutional Neural Networks", "Recurrent Neural Networks", "Transformers",
        "Generative Adversarial Networks", "Autoencoder", "Variational Autoencoder",
        
        # Applications & Domains
        "Chatbot", "Recommendation System", "Autonomous Vehicles",
        "Fraud Detection", "Image Recognition", "Speech Recognition",
        "Sentiment Analysis", "Time Series Forecasting", "Anomaly Detection",
        "Object Detection", "Face Recognition", "Optical Character Recognition",
        "Machine Translation", "Text Summarization", "Question Answering",
        
        # Tools & Frameworks
        "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "Hugging Face",
        "OpenAI", "LangChain", "LlamaIndex", "Vector Database", "Apache Spark",
        "MLflow", "Kubeflow", "Dask", "Ray",
        
        # Ethics & Business
        "AI Ethics", "Explainable AI", "AI Safety", "MLOps", "Data Science",
        "Big Data", "Data Mining", "Business Intelligence", "AI Governance",
        "Fairness in Machine Learning", "AI Bias", "Privacy Preserving ML",
        
        # Advanced Topics
        "Federated Learning", "Quantum Machine Learning", "Neuro-symbolic AI",
        "Causal Inference", "Graph Neural Networks", "Attention Mechanism",
        "Self-supervised Learning", "Multi-task Learning", "Ensemble Learning"
    ]
    
    # Remove duplicates and shuffle
    unique_topics = list(set(ai_ml_topics))
    random.shuffle(unique_topics)
    
    print(f"Attempting to generate {max_docs} documents from {len(unique_topics)} topics...")
    
    for i, title in enumerate(unique_topics):
        if len(documents) >= max_docs:
            break
            
        try:
            print(f"Processing {i+1}/{len(unique_topics)}: {title}")
            
            # Get page with timeout handling
            page = wikipedia.page(title, auto_suggest=False)
            
            # Combine summary and content for better context
            content = page.summary
            if len(content) < 1000:  # If summary is too short, add more content
                content += " " + page.content[:2000]
            
            # Clean content - remove excessive whitespace and special characters
            content = ' '.join(content.split())[:4000]  # Limit to 4000 chars
            
            document = {
                "content": content,
                "metadata": {
                    "title": title,
                    "source": "wikipedia",
                    "category": "AI/ML",
                    "word_count": len(content.split()),
                    "url": page.url,
                    "created_date": fake.date_between(start_date='-3y', end_date='today').isoformat()
                }
            }
            
            documents.append(document)
            used_titles.add(title)
            
        except wikipedia.exceptions.DisambiguationError as e:
            # Try to use disambiguation options
            try:
                # Filter out non-relevant options
                relevant_options = [opt for opt in e.options if any(keyword in opt.lower() for keyword in 
                                    ['machine', 'learning', 'ai', 'artificial', 'neural', 'data'])]
                
                if relevant_options:
                    option = random.choice(relevant_options[:3])
                    if option not in used_titles:
                        page = wikipedia.page(option, auto_suggest=False)
                        content = page.summary[:3000]
                        
                        document = {
                            "content": content,
                            "metadata": {
                                "title": option,
                                "source": "wikipedia",
                                "category": "AI/ML",
                                "word_count": len(content.split()),
                                "url": page.url,
                                "created_date": fake.date_between(start_date='-3y', end_date='today').isoformat()
                            }
                        }
                        documents.append(document)
                        used_titles.add(option)
                        print(f"  → Used disambiguation: {option}")
            except Exception as e:
                print(f"  → Disambiguation failed: {str(e)[:50]}...")
                continue
                
        except wikipedia.exceptions.PageError:
            print(f"  → Page not found: {title}")
            continue
            
        except Exception as e:
            print(f"  → Error with {title}: {str(e)[:50]}...")
            continue
    
    return documents

def enhance_with_enterprise_metadata(documents):
    """Add realistic enterprise metadata with better distribution"""
    departments = ["AI Research", "ML Engineering", "Data Science", "Product", 
                  "Engineering", "R&D", "Analytics", "Platform"]
    
    doc_types = ["Research Paper", "Technical Guide", "API Documentation", "Best Practices", 
                "Implementation Guide", "Technical Report", "System Design", "Tutorial",
                "Whitepaper", "Case Study", "Standard Operating Procedure"]
    
    projects = ["Project Alpha", "Project Beta", "Project Gamma", "Project Orion", 
               "Project Nova", "Project Phoenix", "Project Atlas"]
    
    security_levels = ["Public", "Internal", "Confidential", "Restricted"]
    
    review_statuses = ["approved", "pending", "reviewed", "draft"]
    
    all_tags = ["ai", "ml", "research", "technical", "guide", "tutorial", "framework",
               "algorithm", "model", "data", "analytics", "development", "production"]
    
    for doc in documents:
        # Ensure consistent metadata structure
        doc["metadata"].update({
            "department": random.choice(departments),
            "doc_type": random.choice(doc_types),
            "project": random.choice(projects),
            "security_level": random.choice(security_levels),
            "year": random.randint(2018, 2024),
            "version": f"{random.randint(1, 2)}.{random.randint(0, 5)}",
            "author": fake.name(),
            "confidence_score": round(random.uniform(0.7, 0.98), 2),
            "review_status": random.choice(review_statuses),
            "tags": random.sample(all_tags, random.randint(2, 5))
        })
    
    return documents

def save_documents_to_data_folder(documents, format_type="json"):
    """Save documents to data folder"""
    data_folder = create_data_folder()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format_type == "json":
        filename = os.path.join(data_folder, f"docs_{timestamp}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(documents)} documents to {filename}")
        return filename

def generate_more_documents(target_count=100):
    """Generate additional documents if we need more"""
    print(f"\nGenerating {target_count} documents...")
    
    # First attempt
    documents = get_wikipedia_articles(target_count)
    
    # If we need more, try again with different parameters
    if len(documents) < target_count:
        print(f"Generated {len(documents)} documents. Generating more to reach {target_count}...")
        additional_needed = target_count - len(documents)
        
        # Try with broader search
        additional_docs = get_wikipedia_articles(additional_needed + 10)  # Generate extra
        documents.extend(additional_docs[:additional_needed])
    
    print(f"✅ Successfully generated {len(documents)} documents")
    return documents[:target_count]  # Ensure we don't exceed target

# Main execution
if __name__ == "__main__":
    try:
        # Generate 100 documents
        target_documents = 100
        documents = generate_more_documents(target_documents)
        
        # Enhance with metadata
        documents = enhance_with_enterprise_metadata(documents)
        
        print(f"\n📊 Document Statistics:")
        print(f"Total documents: {len(documents)}")
        print(f"Average word count: {sum(d['metadata']['word_count'] for d in documents) // len(documents)}")
        
        # Show departments distribution
        departments = [d['metadata']['department'] for d in documents]
        print(f"Departments: {set(departments)}")
        
        # Save to data folder
        json_file = save_documents_to_data_folder(documents, "json")
        txt_file = save_documents_to_data_folder(documents, "txt")
        
        print(f"\n🎉 Successfully generated and saved {len(documents)} documents!")
        print(f"JSON file: {json_file}")
        print(f"TXT file: {txt_file}")
        
        # Show sample
        print(f"\n📄 Sample document:")
        sample = documents[0]
        print(f"Title: {sample['metadata']['title']}")
        print(f"Department: {sample['metadata']['department']}")
        print(f"Content preview: {sample['content'][:200]}...")
        
    except Exception as e:
        print(f"❌ Error during document generation: {e}")