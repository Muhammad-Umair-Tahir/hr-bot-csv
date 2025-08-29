import requests
import os
import dotenv
from typing import Dict, List, Optional

dotenv.load_dotenv()
key = os.getenv("RESEARCH_PORTAL_SECRET_KEY")
url = os.getenv("RESEARCH_PORTAL_URL")
api_user = os.getenv("RESEARCH_PORTAL_API_USER")


def fetch_research_portal_data(faculty_code: int) -> Optional[Dict]:
    """
    Fetch specific research portal data for a faculty member.

    Args:
        faculty_code (int): Faculty code/EID

    Returns:
        Dict containing:
        - profile_data: username, full_name, researchgate_url, google_scholar_url
        - articles: list of articles with userid, articleName, articleAcceptanceDate, yearofPublication, status
    """
    try:
        # Use a placeholder URL/key if not set for testing purposes, or ensure .env is configured
        _url = url if url else "http://example.com/api"
        _key = key if key else "dummykey"
        _api_user = api_user if api_user else "dummyuser"

        response = requests.get(f"{_url}/?function=profile&SECRETKEY={_key}&apiuser={_api_user}&eid={faculty_code}")

        if response.status_code != 200:
            print(f"Error: API returned status code {response.status_code}")
            return None

        data = response.json()
        # print("============================================Fetched data:", data, "========================================================")

        # Extract profile data
        profile_data = {
            "username": data['profile'][0]['username'],
            "full_name": data['profile'][0]['full_name'],
            "researchgate_url": data['profile'][0]['researchgate'],
            "google_scholar_url": data['profile'][0]['googleURL']
        }

        # Extract articles data
        articles = []
        # Check if 'Article' key exists and is a dictionary
        if "Article" in data and isinstance(data["Article"], dict):
            # Iterate through the categories (Y, X, W, Other) within 'Article'
            for category_name, article_list_for_category in data["Article"].items():
                # Ensure the category value is actually a list of articles
                if isinstance(article_list_for_category, list):
                    # Iterate through individual articles within each category's list
                    for article in article_list_for_category:
                        article_info = {
                            "userid": article.get("userId"), # Corrected from "userid" to "userId" based on JSON
                            "articleName": article.get("cms_articlename"), # Corrected from "articleName" to "cms_articlename"
                            "articleAcceptanceDate": article.get("cms_articleacceptancedate"), # Corrected
                            "yearofPublication": article.get("cms_yearofpublication"), # Corrected
                            "status": article.get("status")
                        }
                        articles.append(article_info)

        result = {
            "profile_data": profile_data,
            "articles": articles,
            "total_articles": len(articles)
        }

        return result

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except ValueError as e:
        print(f"JSON parsing error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def display_research_data(faculty_code: int) -> None:
    """
    Fetch and display research portal data in a formatted way.

    Args:
        faculty_code (int): Faculty code/EID
    """
    data = fetch_research_portal_data(faculty_code)

    if not data:
        print(f"No data found for faculty code: {faculty_code}")
        return

    profile = data["profile_data"]

    print("=== RESEARCH PORTAL DATA ===")
    print(f"Faculty Code: {faculty_code}")
    print("\n--- Profile Information ---")
    print(f"Username: {profile['username']}")
    print(f"Full Name: {profile['full_name']}")
    print(f"ResearchGate URL: {profile['researchgate_url'] or 'Not provided'}")
    print(f"Google Scholar URL: {profile['google_scholar_url'] or 'Not provided'}")

    print(f"\n--- Articles ({data['total_articles']} found) ---")
    if data["articles"]:
        for i, article in enumerate(data["articles"], 1):
            print(f"\n{i}. Article:")
            print(f"   User ID: {article['userid']}")
            print(f"   Name: {article['articleName']}")
            print(f"   Acceptance Date: {article['articleAcceptanceDate']}")
            print(f"   Year of Publication: {article['yearofPublication']}")
            print(f"   Status: {article['status']}")
    else:
        print("No articles found.")


def get_research_summary(faculty_code: int) -> Optional[Dict]:
    """
    Get a summary of research data for a faculty member.

    Args:
        faculty_code (int): Faculty code/EID

    Returns:
        Dict with research summary or None if no data
    """
    data = fetch_research_portal_data(faculty_code)

    if not data:
        return None

    # Count articles by status
    status_counts = {}
    for article in data["articles"]:
        status = article["status"] or "Unknown"
        status_counts[status] = status_counts.get(status, 0) + 1

    # Get publication years
    publication_years = [
        article["yearofPublication"]
        for article in data["articles"]
        if article["yearofPublication"]
    ]

    summary = {
        "faculty_code": faculty_code,
        "profile": data["profile_data"],
        "total_articles": data["total_articles"],
        "articles_by_status": status_counts,
        "publication_years": sorted(set(publication_years)) if publication_years else [],
        "has_researchgate": bool(data["profile_data"]["researchgate_url"]),
        "has_google_scholar": bool(data["profile_data"]["google_scholar_url"])
    }

    return summary


# Test the function
if __name__ == "__main__":
    # Test with faculty code
    test_faculty_code = 6612

    print("Testing research portal data fetching...")
    display_research_data(test_faculty_code)

    print("\n" + "="*50)

    summary = get_research_summary(test_faculty_code)
    if summary:
        print("\n=== RESEARCH SUMMARY ===")
        print(f"Faculty has ResearchGate profile: {summary['has_researchgate']}")
        print(f"Faculty has Google Scholar profile: {summary['has_google_scholar']}")
        print(f"Total articles: {summary['total_articles']}")
        print(f"Articles by status: {summary['articles_by_status']}")
        print(f"Publication years: {summary['publication_years']}")