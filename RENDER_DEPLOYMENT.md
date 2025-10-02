# Deploy DTCC Trade Analysis to Render.com

This guide will help you deploy your DTCC Trade Analysis application to Render.com.

## Prerequisites

1. A GitHub account
2. A Render.com account (free tier available)
3. Your code pushed to a GitHub repository

## Step 1: Prepare Your Repository

1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Render deployment"
   git branch -M main
   git remote add origin https://github.com/yourusername/your-repo-name.git
   git push -u origin main
   ```

## Step 2: Create Render Account and Connect Repository

1. Go to [render.com](https://render.com) and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub account and select your repository
4. Choose the branch (usually `main`)

## Step 3: Configure the Web Service

### Basic Settings:
- **Name**: `dtcc-trade-analysis` (or your preferred name)
- **Environment**: `Python 3`
- **Region**: Choose closest to your users
- **Branch**: `main`

### Build & Deploy Settings:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main_render.py`

### Environment Variables:
Add these environment variables in the Render dashboard:

```
FLASK_ENV=production
OPENAI_API_KEY=your_openai_api_key_here
```

### Advanced Settings:
- **Plan**: Start with "Starter" (free tier)
- **Auto-Deploy**: Enable if you want automatic deployments on code changes

## Step 4: Add PostgreSQL Database (Optional but Recommended)

1. In Render dashboard, click "New +" → "PostgreSQL"
2. **Name**: `dtcc-db`
3. **Plan**: Start with "Starter" (free tier)
4. **Database Name**: `dtcc_analysis`
5. **User**: `dtcc_user`
6. Click "Create Database"

### Update Environment Variables:
After creating the database, add this environment variable:
```
DATABASE_URL=postgresql://dtcc_user:password@hostname:port/database_name
```
(Render will provide the exact connection string)

## Step 5: Deploy

1. Click "Create Web Service"
2. Render will start building and deploying your application
3. Monitor the build logs for any issues
4. Once deployed, you'll get a URL like `https://your-app-name.onrender.com`

## Step 6: Configure Domain (Optional)

1. Go to your web service settings
2. Click "Custom Domains"
3. Add your custom domain if you have one
4. Follow Render's DNS configuration instructions

## Step 7: Monitor and Maintain

### Health Checks:
- Render automatically monitors your app
- Check the "Logs" tab for any errors
- Monitor the "Metrics" tab for performance

### Scaling:
- Upgrade to a paid plan for better performance
- Configure auto-scaling based on traffic
- Add more resources as needed

## Troubleshooting

### Common Issues:

1. **Build Failures:**
   - Check the build logs in Render dashboard
   - Ensure all dependencies are in `requirements.txt`
   - Verify Python version compatibility

2. **Database Connection Issues:**
   - Verify `DATABASE_URL` environment variable
   - Check if PostgreSQL database is running
   - Ensure database credentials are correct

3. **Application Crashes:**
   - Check the runtime logs
   - Verify all environment variables are set
   - Check for missing dependencies

4. **Memory Issues:**
   - Upgrade to a higher plan
   - Optimize your application code
   - Check for memory leaks

### Logs and Debugging:
- Use `render logs` CLI command
- Check the "Logs" tab in Render dashboard
- Add more logging to your application

## Environment Variables Reference

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `FLASK_ENV` | Flask environment | Yes | `production` |
| `OPENAI_API_KEY` | OpenAI API key for LLM features | No | `sk-proj-...` |
| `DATABASE_URL` | Database connection string | Yes | `postgresql://...` |
| `PORT` | Port number (set by Render) | Auto | `10000` |

## Cost Optimization

### Free Tier Limits:
- 750 hours/month
- 512MB RAM
- Sleeps after 15 minutes of inactivity

### Tips:
- Use the free tier for development/testing
- Upgrade to paid plans for production use
- Monitor usage in the dashboard
- Optimize your application for better performance

## Security Considerations

1. **Environment Variables:**
   - Never commit API keys to your repository
   - Use Render's environment variable system
   - Rotate keys regularly

2. **Database Security:**
   - Use strong passwords
   - Enable SSL connections
   - Regular backups

3. **Application Security:**
   - Keep dependencies updated
   - Use HTTPS (enabled by default on Render)
   - Implement proper error handling

## Support

- Render Documentation: https://render.com/docs
- Render Support: https://render.com/support
- Community Forum: https://community.render.com

## Next Steps

After successful deployment:
1. Test all functionality
2. Set up monitoring and alerts
3. Configure custom domain (if needed)
4. Set up CI/CD pipeline
5. Plan for scaling as your user base grows
