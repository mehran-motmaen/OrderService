# Order Service Setup Guide

This guide provides instructions on setting up and running the Order Service using Docker Compose.

## Prerequisites

Make sure you have the following installed on your machine:

- Docker
- Docker Compose

## Setup Steps

1. **Clone the Repository:**
   ```bash
   git clone 
   cd your-repository


2. **Build and Run Docker Containers:**
  ```bash
   docker-compose up --build
   ```
3. **Access the API:**
  ```bash
   http POST http://localhost:8000/api/orders/ user_id="7c11ee2741" product_code="veggie-box"
  ```
