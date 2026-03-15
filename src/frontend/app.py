import requests
import streamlit as st

API_URL = "http://localhost:8000"  # Use 'localhost:8000' if running locally without Docker Compose

headerSection = st.container()
mainSection = st.container()
loginSection = st.container()
logOutSection = st.container()
signupSection = st.container()

# --- AUTH ---
def LoggedOut_Clicked():
    st.session_state['loggedIn'] = False
    st.session_state['user_id'] = None

def LoggedIn_Clicked(userName, password):
    try:
        resp = requests.post(f"{API_URL}/login", json={"user_id": int(userName), "password": password})
        if resp.status_code == 200:
            st.session_state['loggedIn'] = True
            st.session_state['user_id'] = int(userName)
        else:
            st.session_state['loggedIn'] = False
            st.error("Invalid user name or password")
    except Exception as e:
        st.error(f"Login failed: {e}")

def show_login_page():
    with loginSection:
        if st.session_state['loggedIn'] == False:
            userName = st.text_input("User ID", value="", placeholder="Enter your user id")
            password = st.text_input("Password", value="", placeholder="Enter password", type="password")
            st.button("Login", on_click=LoggedIn_Clicked, args=(userName, password))
            st.markdown("---")
            st.button("Sign Up", on_click=lambda: st.session_state.update({'show_signup': True}))

def show_signup_page():
    with signupSection:
        st.subheader("Sign Up")
        user_id = st.text_input("User ID (numeric)")
        password = st.text_input("Password", type="password")
        gender = st.selectbox("Gender", ["M", "F"])
        age = st.number_input("Age", min_value=1, max_value=120, value=18)
        occupation = st.number_input("Occupation (int)", min_value=0, value=0)
        zipcode = st.text_input("Zipcode")
        if st.button("Register"):
            try:
                resp = requests.post(f"{API_URL}/register", json={
                    "user_id": int(user_id),
                    "password": password,
                    "gender": gender,
                    "age": int(age),
                    "occupation": int(occupation),
                    "zipcode": zipcode
                })
                if resp.status_code == 200:
                    st.success("Registration successful! Please log in.")
                    st.session_state['show_signup'] = False
                else:
                    st.error(resp.json().get('detail', 'Registration failed'))
            except Exception as e:
                st.error(f"Registration failed: {e}")
        if st.button("Back to Login"):
            st.session_state['show_signup'] = False

def show_logout_page():
    loginSection.empty()
    with logOutSection:
        st.button("Log Out", key="logout", on_click=LoggedOut_Clicked)

def show_main_page():
    with mainSection:
        st.subheader("Movie Recommendations")
        user_id = st.session_state.get('user_id')
        if user_id is not None:
            # Fetch recommendations
            try:
                resp = requests.get(f"{API_URL}/recommend/{user_id}")
                if resp.status_code == 200:
                    recs = resp.json()
                    for rec in recs:
                        st.write(f"**{rec['title']}** (Predicted rating: {rec['predicted_rating']:.2f})")
                        if st.button(f"Rate {rec['title']}", key=f"rate_{rec['movie_id']}"):
                            st.session_state['rate_movie_id'] = rec['movie_id']
                else:
                    st.warning("No recommendations found.")
            except Exception as e:
                st.error(f"Failed to fetch recommendations: {e}")
            # Rating form
            if 'rate_movie_id' in st.session_state:
                movie_id = st.session_state['rate_movie_id']
                st.write(f"Rate movie ID: {movie_id}")
                rating = st.slider("Your rating", 1.0, 5.0, 3.0, 0.5)
                if st.button("Submit Rating"):
                    try:
                        resp = requests.post(f"{API_URL}/rate", json={
                            "user_id": user_id,
                            "movie_id": movie_id,
                            "rating": rating
                        })
                        if resp.status_code == 200:
                            st.success("Rating submitted!")
                            del st.session_state['rate_movie_id']
                        else:
                            st.error("Failed to submit rating.")
                    except Exception as e:
                        st.error(f"Failed to submit rating: {e}")

# --- MAIN APP LOGIC ---
with headerSection:
    st.title("MovieLens Recommender App")
    if 'loggedIn' not in st.session_state:
        st.session_state['loggedIn'] = False
    if 'show_signup' not in st.session_state:
        st.session_state['show_signup'] = False
    if st.session_state['show_signup']:
        show_signup_page()
    else:
        if st.session_state['loggedIn']:
            show_logout_page()
            show_main_page()
        else:
            show_login_page()