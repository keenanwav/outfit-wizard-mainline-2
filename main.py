[Previous code up to line 379 remains the same]

            # Save outfit option
            if st.button("Save Outfit"):
                saved_path, success = save_outfit(outfit)
                if success:
                    st.success("Outfit saved successfully!")
                    # Set session state to redirect to Saved Outfits page
                    st.session_state.page = "Saved Outfits"
                    st.experimental_rerun()
                else:
                    st.error("Error saving outfit. Please try again.")

[Previous code from line 387 to line 444 remains the same]

def main():
    """Main application entry point"""
    # Initialize database tables
    create_user_items_table()
    
    # Show first-visit tips
    show_first_visit_tips()
    
    # Check for cleanup needed
    check_cleanup_needed()
    
    # Initialize page in session state if not present
    if 'page' not in st.session_state:
        st.session_state.page = "Generate Outfit"
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Generate Outfit", "My Items", "Saved Outfits"])
    
    # Update session state page if changed by navigation
    if page != st.session_state.page:
        st.session_state.page = page
    
    # Display selected page
    if st.session_state.page == "Generate Outfit":
        main_page()
    elif st.session_state.page == "My Items":
        personal_wardrobe_page()
    else:
        saved_outfits_page()

if __name__ == "__main__":
    main()
