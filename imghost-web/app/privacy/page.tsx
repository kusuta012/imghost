import Head from "next/head";

export default function TermsPage() {
    return (
       <>
       <Head>
        <title>Privacy Policy - ImgHost</title>
        <meta name="description" content="Privacy Policy for ImgHost - what we collect, retention and third-party services" />
       </Head>

       <main className="min-h-screen flex flex-col items-center justify-center p-6 space-y-8">
        <div className="text-center space-y-2">
            <h1 className="text-4xl font-bold tracking-tighter neon-glow">
                IMG<span className="text-accent">HOST</span>
            </h1>
            <div className="flex items-center justify-center space-x-2 text-[10px] uppercase tracking-widest text-zinc-500">
                <span>Privacy Policy</span>
            </div>
        </div>

        <div className="w-full max-w-3xl bg-card border border-border rounded-2xl p-8 shadow-neon">
            <p className="text-zinc-500 text-sm">Last updated: February 17, 2026</p>

            <section className="mt-4">
                <h2 className="text-xl font-semibold">1. What We Collect</h2>
                <p className="mt-2 text-sm text-zinc-300"><strong>Images:</strong></p>
                <ul className="list-disc list-inside mt-2 text-sm text-zinc-300">
                    <li>Images you upload (deleted after 24 hours)</li>
                    <li>Image metadata (file size, format, upload time)</li>
                </ul>

                <p className="mt-2 text-sm text-zinc-300"><strong>Technical Data:</strong></p>
                <ul className="list-disc list-inside mt-2 text-sm text-zinc-300">
                    <li>IP address (for abuse prevention and rate limiting)</li>
                    <li>Browser and device information (via Cloudflare)</li>
                </ul>

                <p className="mt-2 text-sm text-zinc-300"><strong>We do NOT collect:</strong> names, emails (unless you contact us), payment information, or persistent account data.</p>
            </section>

            <section className="mt-4">
                <h2 className="text-xl font-semibold">2. How We Use Your Data</h2>
                <ul className="list-disc list-inside mt-2 text-sm text-zinc-300">
                    <li><strong>IP addresses:</strong> Prevent abuse, enforce rate limits, block bad actors</li>
                    <li><strong>Images:</strong> Provide the hosting service (deleted after 24 hours)</li>
                    <li>Technical data: Monitor service performance via Sentry</li>
                </ul>
            </section>

            <section className="mt-4">
                <h2 className="text-xl font-semibold">3. Third-Party Services</h2>
                <p className="mt-2 text-sm text-zinc-300">
                  We use Cloudflare (CDN/DDoS) and Sentry (error tracking). Those services have their own privacy policies.
                </p>
            </section>
            
            <section className="mt-4">
                <h2 className="text-xl font-semibold">4. Data Retention</h2>
                <ul className="list-disc list-inside mt-2 text-sm text-zinc-300">
                    <li><strong>Images:</strong> Automatically deleted after 24 hours</li>
                    <li><strong>IP addresses</strong> Retained in logs for up to 90 days</li>
                </ul>
            </section>

            <section className="mt-4">
                <h2 className="text-xl font-semibold">5. Your Rights</h2>
                <p className="mt-2 text-sm text-zinc-300">
                 This is an anonymous service. If you need a file removed immediately, contact us with the image link at <a className="text-accent" href="mailto:abuse@imghost.app">abuse@imghost.app</a>
                </p>
            </section>

            <section className="mt-4">
                <h2 className="text-xl font-semibold">6. Security</h2>
                <p className="mt-2 text-sm text-zinc-300">We use HTTPS, Cloudflare protection, and secure file storage. No system is 100% secure.</p>
            </section>

            <section className="mt-4">
                <h2 className="text-xl font-semibold">7. Children's Privacy</h2>
                <p className="mt-2 text-sm text-zinc-300">Not intended for users under 18.</p>
            </section>

            <section className="mt-4">
                <h2 className="text-xl font-semibold">8. International Users</h2>
                <p className="mt-2 text-sm text-zinc-300">Our service is hosted in India. By using it, you consent to data transfer to India.</p>
            </section>

            <section className="mt-4">
                <h2 className="text-xl font-semibold">9. Changes to This Policy</h2>
                <p className="mt-2 text-sm text-zinc-300">We may update this policy at any time; continued use constitutes acceptance of changes.</p>
            </section>

            <section className="mt-4">
                <h2 className="text-xl font-semibold">10. Contact</h2>
                <p className="mt-2 text-sm text-zinc-300">For privacy questions: <a className="text-accent" href="mailto:hi@imghost.app">hi@imghost.app</a></p>
            </section>
            </div>

            <footer className="text-[10px] text-zinc-700 uppercase tracking-[0.2em]">
                SPEEDDD HAWKSSS
            </footer>
       </main>
       </>
    );
}