#!/usr/bin/env python3
"""
ELMA Group Application Runner
Run this script to start the ELMA Group web application.
"""

import os
import sys
from app import create_app

def main():
    """Main function to run the ELMA application."""
    
    # Create Flask app
    app = create_app()
    
    # Set environment variables if not set
    if not os.getenv('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'development'
    
    # Print startup information
    print("=" * 50)
    print("🚀 Starting ELMA Group Application")
    print("=" * 50)
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Debug mode: {app.config.get('DEBUG', False)}")
    print(f"Database: {app.config.get('DATABASE_PATH', 'elma_app.db')}")
    print("=" * 50)
    
    # Initialize database if it doesn't exist
    with app.app_context():
        from app.extensions import db
        try:
            # Try to create tables
            db.create_all()
            print("✅ Database initialized successfully")
            
            # Check if we need to populate with sample data
            from app.models import User, Post, Book
            if User.query.count() == 0:
                print("📚 Database is empty. Populating with sample data...")
                populate_sample_data()
                print("✅ Sample data added successfully")
                
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            print("You may need to manually initialize the database.")
    
    print("🌐 Starting web server...")
    print("🔗 Access the application at: http://localhost:5050")
    print("🔧 Admin panel at: http://localhost:5050/admin")
    print("=" * 50)
    
    # Run the application
    try:
        app.run(host='0.0.0.0', port=5050, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {e}")
        sys.exit(1)

def populate_sample_data():
    """Populate the database with sample data for testing."""
    from app.extensions import db
    from app.models import (
        User, Post, Category, Tag, Book, Author, 
        Publisher, BookCategory, Testimonial, Collection
    )
    from datetime import datetime, timedelta
    import random
    
    # Create admin user
    admin_user = User(
        username='admin',
        email='admin@elmagroup.com',
        first_name='Administrateur',
        last_name='ELMA',
        is_admin=True,
        is_active=True
    )
    admin_user.set_password('admin123')
    db.session.add(admin_user)
    
    # Create blog categories
    blog_categories = [
        Category(name='Littérature Africaine', slug='litterature-africaine', description='Articles sur la littérature du continent africain'),
        Category(name='Économie du Développement', slug='economie-developpement', description='Analyses économiques et développement en Afrique'),
        Category(name='Éducation', slug='education', description='Articles sur l\'éducation et la formation'),
        Category(name='Interviews', slug='interviews', description='Entretiens avec des auteurs et personnalités'),
        Category(name='Actualités', slug='actualites', description='Actualités du groupe ELMA et du secteur')
    ]
    for category in blog_categories:
        db.session.add(category)
    
    # Create blog tags
    blog_tags = [
        Tag(name='Roman', slug='roman'),
        Tag(name='Poésie', slug='poesie'),
        Tag(name='Essai', slug='essai'),
        Tag(name='Jeunesse', slug='jeunesse'),
        Tag(name='Histoire', slug='histoire'),
        Tag(name='Culture', slug='culture'),
        Tag(name='Société', slug='societe'),
        Tag(name='Innovation', slug='innovation')
    ]
    for tag in blog_tags:
        db.session.add(tag)
    
    # Create publishers
    publishers = [
        Publisher(name='ELMA Éditions', slug='elma-editions', description='Maison d\'édition principale du groupe ELMA'),
        Publisher(name='Présence Africaine', slug='presence-africaine', description='Partenaire éditorial historique'),
        Publisher(name='Harmattan Sénégal', slug='harmattan-senegal', description='Filiale sénégalaise de L\'Harmattan')
    ]
    for publisher in publishers:
        db.session.add(publisher)
    
    # Create book categories
    book_categories = [
        BookCategory(name='Romans', slug='romans', description='Romans africains contemporains et classiques'),
        BookCategory(name='Essais', slug='essais', description='Essais sur la société, la politique et l\'économie'),
        BookCategory(name='Poésie', slug='poesie', description='Recueils de poésie africaine'),
        BookCategory(name='Jeunesse', slug='jeunesse', description='Livres pour enfants et adolescents'),
        BookCategory(name='Sciences Humaines', slug='sciences-humaines', description='Ouvrages académiques et de recherche')
    ]
    for category in book_categories:
        db.session.add(category)
    
    # Create authors
    authors = [
        Author(
            name='Mariama Bâ',
            slug='mariama-ba',
            biography='Écrivaine sénégalaise, pionnière de la littérature féminine africaine.',
            nationality='Sénégalaise',
            birth_date=datetime(1929, 4, 17).date()
        ),
        Author(
            name='Aminata Sow Fall',
            slug='aminata-sow-fall',
            biography='Romancière sénégalaise, figure majeure de la littérature africaine contemporaine.',
            nationality='Sénégalaise',
            birth_date=datetime(1941, 4, 27).date()
        ),
        Author(
            name='Boubacar Boris Diop',
            slug='boubacar-boris-diop',
            biography='Écrivain sénégalais, journaliste et intellectuel engagé.',
            nationality='Sénégalaise',
            birth_date=datetime(1946, 10, 3).date()
        )
    ]
    for author in authors:
        db.session.add(author)
    
    # Create collections (exactly 6 as requested)
    collections = [
        Collection(
            name='Littérature',
            slug='litterature',
            description='Romans, nouvelles et récits de la littérature africaine',
            is_featured=True
        ),
        Collection(
            name='Économie du Développement',
            slug='economie-developpement', 
            description='Ouvrages sur l\'économie et le développement en Afrique',
            is_featured=True
        ),
        Collection(
            name='Éducation',
            slug='education',
            description='Manuels scolaires et ressources pédagogiques',
            is_featured=True
        ),
        Collection(
            name='Personnalités',
            slug='personnalites',
            description='Biographies et témoignages de grandes figures africaines',
            is_featured=False
        ),
        Collection(
            name='Entrepreneurs',
            slug='entrepreneurs',
            description='Success stories et guides pour entrepreneurs africains',
            is_featured=False
        ),
        Collection(
            name='Penser l\'Afrique',
            slug='penser-afrique',
            description='Réflexions sur l\'avenir et le développement du continent africain',
            is_featured=False
        )
    ]
    for collection in collections:
        db.session.add(collection)
    
    # Commit to get IDs
    db.session.commit()
    
    # Create sample books
    books_data = [
        {
            'title': 'Une si longue lettre',
            'slug': 'une-si-longue-lettre',
            'description': 'Roman épistolaire qui traite de la condition féminine au Sénégal.',
            'author': authors[0],
            'publisher': publishers[0],
            'category': book_categories[0],
            'price': 15.00,
            'currency': 'EUR'
        },
        {
            'title': 'La Grève des Bàttu',
            'slug': 'la-greve-des-battu',
            'description': 'Roman social qui dénonce la pauvreté urbaine.',
            'author': authors[1],
            'publisher': publishers[0],
            'category': book_categories[0],
            'price': 18.00,
            'currency': 'EUR'
        },
        {
            'title': 'Murambi, le livre des ossements',
            'slug': 'murambi-le-livre-des-ossements',
            'description': 'Roman sur le génocide rwandais.',
            'author': authors[2],
            'publisher': publishers[1],
            'category': book_categories[0],
            'price': 20.00,
            'currency': 'EUR'
        }
    ]
    
    for book_data in books_data:
        book = Book(
            title=book_data['title'],
            slug=book_data['slug'],
            description=book_data['description'],
            price=book_data['price'],
            currency=book_data['currency'],
            availability_status='available',
            publisher_id=book_data['publisher'].id,
            book_category_id=book_data['category'].id
        )
        book.authors.append(book_data['author'])
        book.collections.append(collections[0])  # Add to Literature collection
        db.session.add(book)
    
    # Create sample blog posts
    blog_posts_data = [
        {
            'title': 'La Renaissance de la Littérature Africaine',
            'slug': 'renaissance-litterature-africaine',
            'content': 'La littérature africaine connaît un renouveau remarquable...',
            'excerpt': 'Découvrez les nouvelles voix qui façonnent la littérature africaine contemporaine.',
            'category': blog_categories[0],
            'tags': [blog_tags[0], blog_tags[5]]
        },
        {
            'title': 'L\'Économie Numérique en Afrique',
            'slug': 'economie-numerique-afrique',
            'content': 'Le continent africain est en train de devenir un acteur majeur...',
            'excerpt': 'L\'impact de la révolution numérique sur l\'économie africaine.',
            'category': blog_categories[1],
            'tags': [blog_tags[7], blog_tags[6]]
        },
        {
            'title': 'Interview avec Aminata Sow Fall',
            'slug': 'interview-aminata-sow-fall',
            'content': 'Rencontre avec l\'une des grandes voix de la littérature sénégalaise...',
            'excerpt': 'Entretien exclusif avec la célèbre romancière sénégalaise.',
            'category': blog_categories[3],
            'tags': [blog_tags[0], blog_tags[5]]
        }
    ]
    
    for post_data in blog_posts_data:
        post = Post(
            title=post_data['title'],
            slug=post_data['slug'],
            content=post_data['content'],
            excerpt=post_data['excerpt'],
            published=True,
            author_id=admin_user.id,
            category_id=post_data['category'].id,
            created_at=datetime.now() - timedelta(days=random.randint(1, 30))
        )
        for tag in post_data['tags']:
            post.tags.append(tag)
        db.session.add(post)
    
    # Create sample testimonials
    testimonials_data = [
        {
            'quote': 'ELMA Group publie des livres exceptionnels qui enrichissent notre compréhension de l\'Afrique.',
            'display_name': 'Dr. Fatou Diop',
            'display_title': 'Professeure de Littérature',
            'category': 'Enseignant',
            'is_active': True
        },
        {
            'quote': 'Une maison d\'édition qui valorise vraiment la richesse culturelle africaine.',
            'display_name': 'Mamadou Keita',
            'display_title': 'Libraire',
            'category': 'Libraire',
            'is_active': True
        }
    ]
    
    for testimonial_data in testimonials_data:
        testimonial = Testimonial(**testimonial_data)
        db.session.add(testimonial)
    
    # Final commit
    db.session.commit()
    print("✅ Sample data populated successfully!")

if __name__ == '__main__':
    main()

# For deployment (Gunicorn, Render, etc.)
app = create_app()
