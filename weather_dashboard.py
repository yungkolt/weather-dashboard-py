import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time

# Set page config
st.set_page_config(
    page_title="Weather Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .weather-icon {
        font-size: 3rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

class WeatherAPI:
    """Weather API handler class using multiple free services"""
    
    def __init__(self):
        # Using wttr.in (completely free, no API key needed)
        self.base_url = "https://wttr.in"
        # Alternative: Open-Meteo (also completely free)
        self.openmeteo_url = "https://api.open-meteo.com/v1"
        
    def get_weather_data_wttr(self, city):
        """Fetch current weather data from wttr.in (no API key needed)"""
        try:
            # Get JSON format weather data
            url = f"{self.base_url}/{city}?format=j1"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching weather data from wttr.in: {e}")
            return None
    
    def get_coordinates(self, city):
        """Get coordinates for a city using a free geocoding service"""
        try:
            # Using Open-Meteo's free geocoding API
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('results'):
                return data['results'][0]['latitude'], data['results'][0]['longitude']
            return None, None
        except:
            return None, None
    
    def get_openmeteo_weather(self, lat, lon):
        """Fetch weather data from Open-Meteo (completely free)"""
        try:
            url = f"{self.openmeteo_url}/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code',
                'hourly': 'temperature_2m,relative_humidity_2m,weather_code',
                'daily': 'weather_code,temperature_2m_max,temperature_2m_min',
                'timezone': 'auto',
                'forecast_days': 7
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching data from Open-Meteo: {e}")
            return None

def get_weather_icon_from_code(code):
    """Map weather codes to emojis for different APIs"""
    # WMO Weather interpretation codes (used by Open-Meteo)
    wmo_codes = {
        0: "☀️",   # Clear sky
        1: "🌤️",   # Mainly clear
        2: "⛅",   # Partly cloudy
        3: "☁️",   # Overcast
        45: "🌫️",  # Fog
        48: "🌫️",  # Depositing rime fog
        51: "🌦️",  # Light drizzle
        53: "🌦️",  # Moderate drizzle
        55: "🌧️",  # Dense drizzle
        61: "🌧️",  # Slight rain
        63: "🌧️",  # Moderate rain
        65: "🌧️",  # Heavy rain
        71: "❄️",  # Slight snow
        73: "❄️",  # Moderate snow
        75: "🌨️",  # Heavy snow
        77: "❄️",  # Snow grains
        80: "🌦️",  # Slight rain showers
        81: "🌧️",  # Moderate rain showers
        82: "🌧️",  # Violent rain showers
        85: "🌨️",  # Slight snow showers
        86: "🌨️",  # Heavy snow showers
        95: "⛈️",  # Thunderstorm
        96: "⛈️",  # Thunderstorm with slight hail
        99: "⛈️"   # Thunderstorm with heavy hail
    }
    return wmo_codes.get(code, "🌤️")

def get_weather_description(code):
    """Get weather description from WMO code"""
    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return descriptions.get(code, "Unknown")

def create_temperature_gauge(temp, min_temp=-20, max_temp=50):
    """Create a temperature gauge chart"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = temp,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Temperature (°C)"},
        gauge = {
            'axis': {'range': [min_temp, max_temp]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [-20, 0], 'color': "lightblue"},
                {'range': [0, 20], 'color': "lightgreen"},
                {'range': [20, 35], 'color': "yellow"},
                {'range': [35, 50], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 40
            }
        }
    ))
    fig.update_layout(height=300)
    return fig

def create_forecast_chart(weather_data):
    """Create a forecast line chart using Open-Meteo data"""
    if not weather_data or 'hourly' not in weather_data:
        return None
    
    hourly = weather_data['hourly']
    
    # Get next 24 hours of data
    times = [datetime.fromisoformat(t.replace('Z', '+00:00')) for t in hourly['time'][:24]]
    temps = hourly['temperature_2m'][:24]
    humidity = hourly['relative_humidity_2m'][:24]
    
    # Create subplot
    fig = go.Figure()
    
    # Temperature line
    fig.add_trace(go.Scatter(
        x=times, y=temps,
        mode='lines+markers',
        name='Temperature (°C)',
        line=dict(color='red', width=3),
        yaxis='y'
    ))
    
    # Humidity line on secondary y-axis
    fig.add_trace(go.Scatter(
        x=times, y=humidity,
        mode='lines+markers',
        name='Humidity (%)',
        line=dict(color='blue', width=3),
        yaxis='y2'
    ))
    
    # Update layout
    fig.update_layout(
        title='24-Hour Weather Forecast',
        xaxis_title='Time',
        yaxis=dict(title='Temperature (°C)', side='left'),
        yaxis2=dict(title='Humidity (%)', side='right', overlaying='y'),
        height=400,
        hovermode='x unified'
    )
    
    return fig

def main():
    # Header
    st.markdown('<h1 class="main-header">🌤️ Advanced Weather Dashboard</h1>', 
                unsafe_allow_html=True)
    st.markdown("**Cloud Engineering Weather App** | Real-time weather monitoring with free APIs")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # No API key needed!
        st.success("✅ No API key required!")
        st.info("This dashboard uses completely free weather APIs")
        
        # City selection
        default_cities = ["London", "New York", "Tokyo", "Sydney", "Mumbai", "Las Vegas", "Paris", "Berlin"]
        selected_city = st.selectbox("Select City", default_cities)
        custom_city = st.text_input("Or enter custom city")
        
        city = custom_city if custom_city else selected_city
        
        # API source selection
        api_source = st.radio(
            "Weather Data Source",
            ["Open-Meteo (Recommended)", "wttr.in"],
            help="Both are completely free with no registration required"
        )
        
        # Refresh button
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 🛠️ Features")
        st.markdown("""
        - **API Integration**: Multiple free weather APIs
        - **Error Handling**: Robust exception management
        - **Data Visualization**: Interactive charts
        - **Real-time Monitoring**: Live data updates
        - **Responsive Design**: Mobile-friendly UI
        - **Fallback Systems**: Multiple data sources
        """)
        
        st.markdown("---")
        st.markdown("### 🌐 Free APIs Used")
        st.markdown("""
        - **Open-Meteo**: Professional weather API
        - **wttr.in**: Terminal-style weather service
        - **No registration required!**
        """)
    
    # Initialize weather API
    weather_api = WeatherAPI()
    
    # Fetch data based on selected source
    with st.spinner(f"Fetching weather data for {city}..."):
        if api_source == "Open-Meteo (Recommended)":
            # Get coordinates first
            lat, lon = weather_api.get_coordinates(city)
            if lat and lon:
                weather_data = weather_api.get_openmeteo_weather(lat, lon)
                data_source = "open-meteo"
            else:
                st.error(f"❌ Could not find coordinates for {city}")
                return
        else:
            weather_data = weather_api.get_weather_data_wttr(city)
            data_source = "wttr"
    
    if not weather_data:
        st.error("❌ Failed to fetch weather data. Please try a different city or data source.")
        return
    
    # Process and display data based on source
    if data_source == "open-meteo":
        current = weather_data['current']
        daily = weather_data['daily']
        
        # Current weather metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            temp = current['temperature_2m']
            st.metric(
                label="🌡️ Temperature",
                value=f"{temp:.1f}°C"
            )
        
        with col2:
            humidity = current['relative_humidity_2m']
            st.metric(
                label="💧 Humidity",
                value=f"{humidity}%"
            )
        
        with col3:
            wind_speed = current['wind_speed_10m']
            st.metric(
                label="💨 Wind Speed",
                value=f"{wind_speed:.1f} km/h"
            )
        
        with col4:
            weather_code = current['weather_code']
            weather_desc = get_weather_description(weather_code)
            st.metric(
                label="🌤️ Condition",
                value=weather_desc.split()[0]  # First word only for space
            )
        
        # Weather description and icon
        weather_icon = get_weather_icon_from_code(weather_code)
        
    else:  # wttr.in data
        current_condition = weather_data['current_condition'][0]
        
        # Current weather metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            temp = float(current_condition['temp_C'])
            feels_like = float(current_condition['FeelsLikeC'])
            st.metric(
                label="🌡️ Temperature",
                value=f"{temp:.1f}°C",
                delta=f"Feels like {feels_like:.1f}°C"
            )
        
        with col2:
            humidity = current_condition['humidity']
            st.metric(
                label="💧 Humidity",
                value=f"{humidity}%"
            )
        
        with col3:
            wind_speed = current_condition['windspeedKmph']
            st.metric(
                label="💨 Wind Speed",
                value=f"{wind_speed} km/h"
            )
        
        with col4:
            visibility = current_condition['visibility']
            st.metric(
                label="👁️ Visibility",
                value=f"{visibility} km"
            )
        
        # Weather description and icon
        weather_desc = current_condition['weatherDesc'][0]['value']
        weather_icon = "🌤️"  # Default icon for wttr.in
    
    st.markdown("---")
    
    # Main dashboard row
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"""
        <div class="weather-icon">
            {weather_icon}
        </div>
        <h3 style="text-align: center;">{weather_desc}</h3>
        <p style="text-align: center; color: #666;">
            {city}<br>
            Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <small>Data source: {api_source}</small>
        </p>
        """, unsafe_allow_html=True)
        
        # Temperature gauge
        if data_source == "open-meteo":
            gauge_fig = create_temperature_gauge(current['temperature_2m'])
        else:
            gauge_fig = create_temperature_gauge(float(current_condition['temp_C']))
        st.plotly_chart(gauge_fig, use_container_width=True)
    
    with col2:
        # Forecast chart (only available for Open-Meteo)
        if data_source == "open-meteo":
            forecast_fig = create_forecast_chart(weather_data)
            if forecast_fig:
                st.plotly_chart(forecast_fig, use_container_width=True)
        else:
            st.info("📊 Hourly forecast charts available with Open-Meteo source")
            # Show today's forecast from wttr.in
            today_weather = weather_data['weather'][0]
            st.markdown("### Today's Forecast")
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Max:** {today_weather['maxtempC']}°C")
                st.write(f"**Min:** {today_weather['mintempC']}°C")
            with col_b:
                st.write(f"**UV Index:** {today_weather['uvIndex']}")
                if 'astronomy' in today_weather:
                    sunrise = today_weather['astronomy'][0]['sunrise']
                    sunset = today_weather['astronomy'][0]['sunset']
                    st.write(f"**Sunrise:** {sunrise}")
                    st.write(f"**Sunset:** {sunset}")
    
    # 5-day forecast
    st.markdown("---")
    st.subheader("📅 Extended Forecast")
    
    if data_source == "open-meteo":
        # Open-Meteo daily forecast
        daily_data = weather_data['daily']
        forecast_cols = st.columns(5)
        
        for i in range(5):
            with forecast_cols[i]:
                date = datetime.fromisoformat(daily_data['time'][i]).strftime('%a %m/%d')
                max_temp = daily_data['temperature_2m_max'][i]
                min_temp = daily_data['temperature_2m_min'][i]
                weather_code = daily_data['weather_code'][i]
                icon = get_weather_icon_from_code(weather_code)
                condition = get_weather_description(weather_code)
                
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; border: 1px solid #ddd; border-radius: 0.5rem;">
                    <strong>{date}</strong><br>
                    <div style="font-size: 2rem;">{icon}</div>
                    <small>{condition}</small><br>
                    <strong>{max_temp:.0f}°/{min_temp:.0f}°</strong>
                </div>
                """, unsafe_allow_html=True)
    
    else:
        # wttr.in forecast (up to 3 days)
        forecast_cols = st.columns(min(3, len(weather_data['weather'])))
        
        for i, day_weather in enumerate(weather_data['weather'][:3]):
            with forecast_cols[i]:
                if i == 0:
                    date = "Today"
                elif i == 1:
                    date = "Tomorrow"
                else:
                    date = f"Day {i+1}"
                
                max_temp = day_weather['maxtempC']
                min_temp = day_weather['mintempC']
                condition = day_weather['hourly'][4]['weatherDesc'][0]['value']  # Midday weather
                
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; border: 1px solid #ddd; border-radius: 0.5rem;">
                    <strong>{date}</strong><br>
                    <div style="font-size: 2rem;">🌤️</div>
                    <small>{condition}</small><br>
                    <strong>{max_temp}°/{min_temp}°</strong>
                </div>
                """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>Built with Python, Streamlit, and Free Weather APIs</p>
        <p>No API keys required! | Data from {api_source}</p>        
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()