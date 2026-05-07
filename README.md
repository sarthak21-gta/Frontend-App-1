# Parking Management System

A comprehensive web-based parking management system built with Python and Flask. This project provides a user-friendly interface to manage cars, parking lots, active parking sessions, and payments.

This version uses **Supabase** (PostgreSQL) as the backend database for reliable data storage and easy cloud hosting.

## Features

- **Dashboard**: Get a quick overview of total cars, active parkings, available parking lots, and daily revenue.
- **Parking Lots Management**: View, filter (occupied/unoccupied), create, edit, and delete parking spots.
- **Cars Management**: Register new cars, edit existing car details, and track their complete parking history.
- **Parkings**: Start new parking sessions, assign cars to parking lots, end sessions, and automatically generate payments.
- **Payments Processing**: Keep track of paid and pending payments for all parking sessions.

## Technologies Used

- **Language**: Python 3
- **Web Framework**: Flask
- **Database**: Supabase (PostgreSQL)
- **Frontend**: Classic CSS (Vanilla) & Jinja2 Templates

## Setup and Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd parking-management-main
    ```

2.  **Install dependencies**:
    ```bash
    pip install Flask supabase python-dotenv
    ```

3.  **Supabase Setup**:
    -   Create a new project on [Supabase](https://supabase.com).
    -   Use the Supabase CLI or Dashboard to run the migration found in `supabase/migrations/`.
    -   Copy `.env.example` to `.env` and fill in your `SUPABASE_URL` and `SUPABASE_KEY`.

4.  **Run the application**:
    ```bash
    python main.py
    ```

5.  **Access the application**:
    Open `http://127.0.0.1:5000/` in your browser.

## Database Migration

If you have the Supabase CLI installed, you can link your project and apply the migrations:

```bash
supabase login
supabase link --project-ref your-project-ref
supabase db push
```
site link https://parking-management-main.vercel.app/login

