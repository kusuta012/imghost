import Head from "next/head";

export default function TermsPage() {
    return (
        <>
        <Head>
            <title>Terms of Use - ImgHost</title>
            <meta name="description" content="Terms of Use for ImgHost" />
        </Head>

        <main className="min-h-screen flex flex-col items-center justify-center p-6 space-y-8">
            <div className="text-center space-y-2">
                <h1 className="text-4xl font-bold tracking-tighter neon-glow">
                    IMG<span className="text-accent">HOST</span>
                </h1>
                <div className="flex items-center justify-center space-x-2 text-[10px] uppercase tracking-widest text-zinc-500">
                    <span>Terms of Use</span>
                </div>
            </div>

            <div className="w-full max-w-3xl bg-card border border-border rounded-2xl p-8 shadow-neon">
                <p className="text-zinc-500 text-sm">Last updated: February 17, 2026</p>
                <section className="mt-4">
                    <h2 className="text-xl font-semibold">1. Service Overview</h2>
                    <p className="mt-2 text-sm text-zinc-300">
                        ImgHost provides a free, anonymous image hosting service at speedhawks.online Images uploaded are
                        automatically deleted after 24 hours. By using our service you agree to these Terms of Use.
                    </p>
                </section>

                <section className="mt-4">
                    <h2 className="text-xl font-semibold">2. How It Works</h2>
                    <ul className="list-disc list-inside mt-2 text-sm text-zinc-300">
                        <li>Upload Images without creating an account.</li>
                        <li>Each image receives a unique link.</li>
                        <li>All images are automatically deleted after 24 hours.</li>
                        <li>We do not track who uploads what beyond short-lived metadata used for abuse prevention.</li>
                    </ul>
                </section>

                <section className="mt-4">
                    <h2 className="text-xl font-semibold">3. What You Cannot Upload</h2>
                    <p className="mt-2 text-sm text-zinc-300">You may not upload images that contain any of the following:</p>
                    <ul className="list-disc list-inside mt-2 text-sm text-zinc-300">
                        <li>Child sexual abuse material (CSAM) or content exploiting minors</li>
                        <li>Non-consensual intimate images or revenge porn</li>
                        <li>Content that infringes copyright or intellectual property rights</li>
                        <li>Graphic violence, gore, or shock content</li>
                        <li>Hate speech or content promoting violence</li>
                        <li>Content used for harassment, doxxing, or abuse</li>
                        <li>Any other illegal content</li>
                    </ul>
                    <p className="text-sm text-zinc-400 mt-2">Violations will result in immediate removal and may be reported to authorities.</p>
                </section>

                <section className="mt-4">
                    <h2 className="text-xl font-semibold">4. Service Rules</h2>
                    <ul className="list-disc list-inside mt-2 text-sm text-zinc-300">
                        <li>Do not use automated tools or bots to bulk upload images</li>
                        <li>Do not attempt to bypass the 24-hour deletion system</li>
                        <li>Do not hotlink images to abuse our bandwidth</li>
                        <li>Do not use the service for phishing, fraud, or spam</li>
                        <li>Do not use the service for any illegal purpose</li>
                    </ul>
                </section>

                <section className="mt-4">
                    <h2 className="text-xl font-semibold">5. Content Rights</h2>
                    <ul className="list-disc list-inside mt-2 text-sm text-zinc-300">
                        <li>You retain all rights to your uploaded images.</li>
                        <li>By uploading, you grant us the right to host and display your images for 24 hours.</li>
                        <li>We may remove any content that violates these terms at any time.</li>
                    </ul>
                </section>

                <section className="mt-4">
                    <h2 className="text-xl font-semibold">6. Liability &amp; Disclaimers</h2>
                    <p className="mt-2 text-sm text-zinc-300">
                        This is a free service provided "as is" without warranties. We are not responsible for content users upload and
                        are not liable for any damages resulting from your use of the service.
                    </p>
                </section>

                <section className="mt-4">
                    <h2 className="text-xl font-semibold">7. Reporting Abuse</h2>
                    <p className="mt-2 text-sm text-zinc-300">
                        Report illegal or abusive content to: <a className="text-accent" href="mailto:abuse@speedhawks.online">abuse@speedhawks.online</a>
                    </p>
                </section>

                <section className="mt-4">
                    <h2 className="text-xl font-semibold">8. Governing Law</h2>
                    <p className="mt-2 text-sm text-zinc-300">These terms are governed by the laws of India.</p>
                </section>

                <section className="mt-4">
                    <h2 className="text-xl font-semibold">9. Contact</h2>
                    <p className="mt-2 text-sm text-zinc-300">Email: <a className="text-accent" href="mailto:hi@speedhawks.online">hi@speedhawks.online</a></p>
                </section>
            </div>

            <footer className="text-[10px] text-zinc-700 uppercase tracking-[0.2em]">
                SPEEDDD HAWKSSS
            </footer>
        </main>
        </>
    );
}