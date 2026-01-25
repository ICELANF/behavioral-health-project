import 'reflect-metadata';
import { DataSource, DataSourceOptions } from 'typeorm';
import { config } from 'dotenv';
import * as path from 'path';

// Load environment variables
config();

const isProduction = process.env.NODE_ENV === 'production';

const baseConfig: DataSourceOptions = {
  type: 'postgres',
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  username: process.env.DB_USER || 'bhp_user',
  password: process.env.DB_PASSWORD || 'bhp_secure_password',
  database: process.env.DB_NAME || 'behavioral_health',
  entities: [path.join(__dirname, '../entities/*.entity.{ts,js}')],
  migrations: [path.join(__dirname, '../migrations/*.{ts,js}')],
  synchronize: false, // Always use migrations
  logging: !isProduction,
  ssl: isProduction ? { rejectUnauthorized: false } : false,
};

export const AppDataSource = new DataSource(baseConfig);

/**
 * Initialize database connection
 */
export async function initializeDatabase(): Promise<DataSource> {
  if (!AppDataSource.isInitialized) {
    try {
      await AppDataSource.initialize();
      console.log('✅ Database connection established');
    } catch (error) {
      console.error('❌ Database connection failed:', error);
      throw error;
    }
  }
  return AppDataSource;
}

/**
 * Close database connection
 */
export async function closeDatabase(): Promise<void> {
  if (AppDataSource.isInitialized) {
    await AppDataSource.destroy();
    console.log('Database connection closed');
  }
}
