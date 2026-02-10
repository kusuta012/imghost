import { hostname } from 'os';

/** @type {import('next').NextConfig} */
const NextConfig = {
    images: {
        remotePatterns: [
            {
                protocol: 'https',
                hostname: '**',
            },
        ],
    },
};

export default NextConfig;