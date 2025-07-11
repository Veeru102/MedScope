#!/usr/bin/env python3
"""
Generate a larger synthetic arXiv dataset with 200+ medical AI papers.
This creates realistic-looking paper entries to test the search functionality.
"""

import csv
import random
from datetime import datetime, timedelta

# Medical AI topics and templates
topics = [
    "Deep Learning", "Machine Learning", "Computer Vision", "Natural Language Processing",
    "Medical Imaging", "Radiology", "Pathology", "Dermatology", "Cardiology", "Neurology",
    "Oncology", "Ophthalmology", "Genomics", "Drug Discovery", "Clinical Decision Support",
    "Telemedicine", "Wearable Devices", "IoT Healthcare", "Federated Learning", "Privacy",
    "Explainable AI", "Transfer Learning", "Few-shot Learning", "Multi-modal", "Transformer",
    "CNN", "RNN", "GAN", "VAE", "Reinforcement Learning", "Graph Neural Networks",
    "Brain Tumor", "Lung Cancer", "Breast Cancer", "Skin Cancer", "Diabetic Retinopathy",
    "COVID-19", "Alzheimer's", "Parkinson's", "Multiple Sclerosis", "Heart Disease"
]

# Title templates
title_templates = [
    "{} for {} Detection Using {}",
    "Automated {} Diagnosis with {} Techniques",
    "AI-Assisted {} Analysis in {} Applications", 
    "Novel {} Approach for {} Classification",
    "{}-Based {} Screening and Diagnosis",
    "Advanced {} Methods for {} Prediction",
    "Intelligent {} System for {} Monitoring",
    "{} Techniques in {} Image Analysis",
    "Precision {} Using {} and {}",
    "Real-time {} Detection with {} Networks",
    "Robust {} Framework for {} Assessment",
    "Multi-modal {} for {} Characterization",
    "Federated {} in {} Healthcare",
    "Explainable {} for {} Decision Making",
    "Transfer {} Approach to {} Recognition"
]

# Abstract templates
abstract_templates = [
    "This paper presents a novel {} approach for {} in medical applications. We propose a {}-based framework that achieves state-of-the-art performance on {} datasets. Our method demonstrates {}% accuracy improvement over existing techniques. The approach addresses challenges in {} and shows promise for clinical deployment. Experimental validation on {} patients confirms the effectiveness of our methodology.",
    
    "We introduce an innovative {} system for automated {} analysis. The proposed method combines {} with {} to enhance diagnostic accuracy. Our approach was evaluated on a dataset of {} samples, achieving {}% sensitivity and {}% specificity. The results demonstrate significant potential for improving {} workflows and patient outcomes.",
    
    "This study explores the application of {} techniques to {} diagnosis. We develop a comprehensive framework that integrates {} and {} for robust disease detection. The method was validated using {} images from multiple medical centers. Our approach outperforms existing methods by {}% in terms of diagnostic accuracy.",
    
    "We present a {} architecture for {} classification in medical imaging. The model employs {} to capture complex patterns and achieves superior performance on {} benchmark datasets. Our method addresses key challenges in {} and demonstrates {}% improvement in clinical metrics. The approach shows promise for real-world deployment.",
    
    "This paper investigates {} methods for {} prediction in healthcare. We propose a novel {} framework that leverages {} to improve diagnostic capabilities. Experiments on {} patient records demonstrate {}% accuracy and excellent generalization across different populations. The method offers significant potential for clinical decision support."
]

# Author name components
first_names = [
    "John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa", "William", "Maria",
    "James", "Jennifer", "Christopher", "Michelle", "Daniel", "Elizabeth", "Thomas", "Jessica",
    "Matthew", "Ashley", "Andrew", "Amanda", "Joshua", "Stephanie", "Ryan", "Nicole", "Kevin",
    "Rachel", "Brian", "Laura", "Mark", "Katherine", "Steven", "Rebecca", "Timothy", "Helen",
    "Paul", "Angela", "Kenneth", "Sophia", "Richard", "Emma", "Charles", "Olivia", "Joseph",
    "Anna", "Anthony", "Patricia", "Alan", "Linda", "Benjamin", "Barbara"
]

last_names = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez",
    "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor",
    "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez",
    "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright",
    "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson", "Baker",
    "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts", "Gomez", "Phillips",
    "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards", "Collins", "Reyes", "Stewart",
    "Morris", "Morales", "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan",
    "Cooper", "Peterson", "Bailey", "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox",
    "Ward", "Richardson", "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett"
]

categories = [
    "cs.CV", "cs.AI", "cs.LG", "stat.ML", "cs.CL", "eess.IV", "q-bio.QM", "q-bio.NC",
    "physics.med-ph", "cs.HC", "cs.IR", "cs.NE", "cs.RO", "stat.AP"
]

def generate_author_name():
    """Generate a realistic author name."""
    first = random.choice(first_names)
    last = random.choice(last_names)
    return f"{first} {last}"

def generate_authors():
    """Generate 1-5 co-authors."""
    num_authors = random.randint(1, 5)
    authors = []
    for _ in range(num_authors):
        authors.append(generate_author_name())
    return ", ".join(authors)

def generate_title():
    """Generate a realistic paper title."""
    template = random.choice(title_templates)
    
    # Fill in the template with random topics
    if template.count('{}') == 2:
        topic1 = random.choice(topics)
        topic2 = random.choice(topics)
        while topic2 == topic1:
            topic2 = random.choice(topics)
        return template.format(topic1, topic2)
    elif template.count('{}') == 3:
        topic1 = random.choice(topics)
        topic2 = random.choice(topics)
        topic3 = random.choice(topics)
        while topic2 == topic1:
            topic2 = random.choice(topics)
        while topic3 in [topic1, topic2]:
            topic3 = random.choice(topics)
        return template.format(topic1, topic2, topic3)
    else:
        # For templates with more placeholders, just use random topics
        topic_list = random.sample(topics, min(template.count('{}'), len(topics)))
        return template.format(*topic_list)

def generate_abstract():
    """Generate a realistic abstract."""
    template = random.choice(abstract_templates)
    
    # Fill in the template
    method = random.choice(["deep learning", "machine learning", "neural network", "CNN", "transformer"])
    application = random.choice(["cancer detection", "medical imaging", "diagnosis", "screening", "classification"])
    technique1 = random.choice(["attention mechanism", "transfer learning", "data augmentation", "ensemble methods"])
    technique2 = random.choice(["computer vision", "feature extraction", "pattern recognition", "image segmentation"])
    num_samples = random.randint(1000, 50000)
    accuracy = random.randint(85, 98)
    sensitivity = random.randint(80, 96)
    specificity = random.randint(82, 97)
    improvement = random.randint(5, 25)
    workflow = random.choice(["clinical", "diagnostic", "screening", "treatment planning"])
    
    return template.format(
        method, application, technique1, technique2, num_samples,
        accuracy, sensitivity, specificity, workflow, improvement
    )

def generate_arxiv_id(year):
    """Generate a realistic arXiv ID."""
    month = random.randint(1, 12)
    paper_num = random.randint(1000, 9999)
    return f"{year-2000:02d}{month:02d}.{paper_num}"

def generate_year():
    """Generate a year between 2020-2024."""
    return random.randint(2020, 2024)

def generate_dataset(num_papers=250):
    """Generate a dataset with the specified number of papers."""
    papers = []
    
    for i in range(num_papers):
        year = generate_year()
        paper = {
            'id': generate_arxiv_id(year),
            'title': generate_title(),
            'abstract': generate_abstract(),
            'authors': generate_authors(),
            'year': year,
            'categories': ", ".join(random.sample(categories, random.randint(1, 3)))
        }
        papers.append(paper)
    
    return papers

def main():
    """Generate the dataset and save to CSV."""
    print("Generating larger arXiv dataset with 250 medical AI papers...")
    
    papers = generate_dataset(250)
    
    # Save to CSV
    output_file = "data/arxiv_sample.csv"
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'title', 'abstract', 'authors', 'year', 'categories']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for paper in papers:
            writer.writerow(paper)
    
    print(f"Successfully generated {len(papers)} papers and saved to {output_file}")
    print("Sample titles:")
    for i, paper in enumerate(papers[:5]):
        print(f"{i+1}. {paper['title']}")

if __name__ == "__main__":
    main() 