from hybrid_agent import run_hybrid_search

def main():
    """
    Main entry point of the application.
    Prompts the user for a query and initiates the hybrid search.
    """
    user_query = input("Please describe your recent life experience in a few sentences:\n> ").strip()
    if user_query:
        run_hybrid_search(user_query)

if __name__ == "__main__":
    main()



    # Test query: I just moved to Raleigh, North Carolina and I'm excited for the fresh start that I have. The nature is so beautiful here. I've already made a great group of friends through my new job and I couldn't be happier or feel more free. 
    # It's raining outside heavily and I feel so comfortable. I'm staying in and cuddling with my girlfriend in candlelight. We'll get under blankets and watch tv or just talk, and enjoy each other's company.
    # I hate my life. All my friends are assholes. My boss is a jerk. Everyone is so surface level. I don't get paid enough to be here.
    # I'm at the beach drinking with my long-time friends on the weekend. It's relaxed and we're playing volleyball and the music is turned up loud. Country music
    