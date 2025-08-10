import React, { useState, useEffect } from 'react';
import { useState, useEffect } from 'react';
import { apiService } from '../../../services/apiService';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';

export const AnalyticsDashboard = () => {
    const [analytics, setAnalytics] = useState(null);
    const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchAnalytics();
        }, [selectedYear]
    ); 

    const fetchAnalytics = async () => {
        try {
            setIsLoading(true);
            const [topSellers, monthlyData] = await Promise.all([
                apiService.getTopSellers(selectedYear),
                apiService.getMonthlyAnalytics(selectedYear)
            ]);

            setAnalytics({
                topSellers,
                monthlyData: monthlyData
                .map((item) => ({
                    month: item.month,
                    sales: item.total_sales,
                    orders: item.total_orders,
                    revenue: item.total_revenue
                }))
            });
        } catch (error) {
            console.error('Failed to fetch analytics:', error);
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return (
            <div className="animate-pulse">
                LoadingLoading analytics...
            </div>
        );
    }

    return (
         <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold">Shop Analytics</h1>
                <select
                    value={selectedYear}
                    onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                    className="border rounded-lg px-4 py-2"
                >
                    {[2024, 2023, 2022].map((year) => (
                        <option key={year} value={year}>
                            {year}
                        </option>
                    ))}
                </select>
            </div>

            {/* Revenue Chart */}
            <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold mb-4">Monthly Revenue</h2>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={analytics?.monthlyData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip />
                        <Line type="monotone" dataKey="revenue" stroke="#3B82F6" strokeWidth={2} />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Top Sellers Grid */}
            <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold mb-4">Top Selling Items</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {analytics?.topSellers?.map((item, index) => (
                        <div key={item.listing_id} className="border rounded-lg p-4">
                            <img
                                src={item.image_url}
                                alt={item.title}
                                className="w-full h-32 object-cover rounded mb-2"
                            />
                            <h3 className="font-medium truncate">{item.title}</h3>
                            <p className="text-gray-600">${item.price}</p>
                            <p className="text-sm text-green-600">{item.total_sales} sales</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

   