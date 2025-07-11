import instaloader
import pymongo
import os
import datetime
import json

# --- Instagram Configuration ---
USERNAME = 'amine.dev'                # Your Instagram username
PASSWORD = 'AmineSecurePass2025'      # Your Instagram password
TARGET_HASHTAG = 'jacqueschirac'      # The hashtag you want to scrape
POST_LIMIT = 50                       # Number of posts to scrape
DOWNLOAD_IMAGES = True                # Set to False if you don't want to download images
IMAGE_DIR = 'scraped_images'          # Directory to save images

# --- MongoDB Configuration ---
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DB_NAME = 'instagram_data'
MONGO_COLLECTION_NAME = 'posts'

def scrape_instagram():
    # Initialize Instaloader
    L = instaloader.Instaloader()

    try:
        # Load session or login
        L.load_session_from_file(USERNAME)
    except FileNotFoundError:
        print(f"Session file not found for {USERNAME}. Logging in...")
        try:
            L.login(USERNAME, PASSWORD)
            L.save_session_to_file() # Save session for future use
        except Exception as e:
            print(f"Error logging in to Instagram: {e}")
            return

    # Connect to MongoDB
    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    db = client[MONGO_DB_NAME]
    collection = db[MONGO_COLLECTION_NAME]

    # Create image directory if it doesn't exist
    if DOWNLOAD_IMAGES and not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    print(f"Scraping posts for hashtag: #{TARGET_HASHTAG}...")
    posts_scraped = 0

    try:
        for post in L.get_hashtag_posts(TARGET_HASHTAG):
            if posts_scraped >= POST_LIMIT:
                break

            print(f"Processing post: {post.shortcode}")

            image_path = None
            if DOWNLOAD_IMAGES:
                try:
                    # Download post data including media
                    L.download_post(post, target=IMAGE_DIR)
                    image_filename_prefix = f"{post.date_utc.strftime('%Y-%m-%d_%H-%M-%S')}_UTC"
                    # Look for files that start with the prefix and contain the shortcode
                    found_files = [f for f in os.listdir(IMAGE_DIR) if f.startswith(image_filename_prefix) and str(post.shortcode) in f]
                    if found_files:
                        image_path = os.path.join(IMAGE_DIR, found_files[0]) # Take the first match
                    else:
                        print(f"Could not infer exact image path for {post.shortcode}. Image might be in a subfolder.")

                except Exception as e:
                    print(f"Could not download image for {post.shortcode}: {e}")
                    image_path = None

            comments_list = []
            for comment in post.get_comments():
                comments_list.append({
                    'owner': comment.owner.username,
                    'text': comment.text,
                    'created_at': comment.created_at_utc
                })

            post_data = {
                'post_id': post.shortcode,
                'caption': post.caption,
                'owner_username': post.owner_username,
                'likes': post.likes,
                'comments_count': post.comments,
                'date_utc': post.date_utc,
                'image_path': image_path, # Path to the downloaded image
                'comments': comments_list
            }

            # Insert into MongoDB
            try:
                collection.insert_one(post_data)
                print(f"Inserted post {post.shortcode} into MongoDB.")
                posts_scraped += 1
            except pymongo.errors.DuplicateKeyError:
                print(f"Post {post.shortcode} already exists in MongoDB.")
            except Exception as e:
                print(f"Error inserting post {post.shortcode} into MongoDB: {e}")

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
    finally:
        print(f"Scraping finished. Total posts processed: {posts_scraped}")
        client.close()

if __name__ == '__main__':
    # IMPORTANT: Replace with your actual Instagram username and password.
    scrape_instagram()
