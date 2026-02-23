
# [Imghost](https://imghost.app)

Imghost is a temporary(upto 24hrs) image hosting service. It supports various types of images like JPEG, PNG, WEBP, HEIF/HEIC, GIF. You can set your own time for expiry. Its has blazing fast upload speeds with 2 stage image compression but you still get the highest quality.

## Why This Exists

I used to rely on host.systems for quick image uploads and sharing. When it shut down, I realized I needed something I could actually depend on. So I built this - a simple, self-hosted alternative that does what I need without the bloat.

## Features

- **Smart compression** - Automatically converts images to WebP (except GIFs, those stay animated)
- **Flexible expiration** - Set links to expire anywhere from 5 minutes to 24hrs
- **Multi-upload** - Drop up to 15 files at once
- **GIF support** - Upload animated GIFs up to 25MB without losing frames
- **Themes** - Multiple themes because why not
- **Rate limiting** - Built-in protection against abuse
- **S3 storage** - Works with any S3-compatible storage (Cloudflare R2, AWS S3, etc.)

## Techstack

**Frontend:**
- Next.js 14
- TypeScript
- Tailwind CSS
- Framer Motion

**Backend:**
- FastAPI
- PostgreSQL
- Pillow (image processing)

**Storage:**
- S3-compatible (I use OCI Object Storage)

## Showcase

<img width="1920" height="974" alt="image" src="https://github.com/user-attachments/assets/071fd59a-cd49-452c-a4b5-31e397b20880" />
<img width="1920" height="975" alt="image" src="https://github.com/user-attachments/assets/f1449af7-29f2-498e-b313-bface84fe0b1" />
<img width="1918" height="974" alt="image" src="https://github.com/user-attachments/assets/06b70174-057e-4bd3-9340-d245fb9968a7" />
<img width="1920" height="979" alt="uploading" src="https://github.com/user-attachments/assets/8ef9dd5f-5d55-4a36-a969-e7b0dc1f837d" />
<img width="1920" height="977" alt="uploaded" src="https://github.com/user-attachments/assets/17adf5c8-7aa9-4235-9829-813bf5a9cd49" />

## Declaration

- Claude used for minor bugs , system design and planning.
- Copilot for tabcompletion and refactoring the frontend.


