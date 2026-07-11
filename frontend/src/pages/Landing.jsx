import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Ruler,
  MessagesSquare,
  BadgeCheck,
  ShieldCheck,
  Star,
} from 'lucide-react'
import Marquee from '../components/Marquee'

const STEPS = [
  {
    icon: Ruler,
    title: 'Share four measurements',
    text: 'Chest, waist, hips, and height — entered once, saved as your Fit Passport for every product after.',
  },
  {
    icon: MessagesSquare,
    title: 'We read the reviews for you',
    text: 'Thousands of buyer reviews are mined for fit signals: runs small, tight shoulders, long in the leg.',
  },
  {
    icon: BadgeCheck,
    title: 'Get one honest answer',
    text: 'A recommended size with a fit score, a tight-to-loose breakdown per dimension, and the caveats spelled out.',
  },
]

const TESTIMONIALS = [
  { quote: 'Fits perfectly, true to size!', user: 'aisyah_', product: 'Classic Oxford Shirt' },
  { quote: 'Perfect fit, great stretch for denim.', user: 'denim_dan', product: 'Slim Tapered Jeans' },
  { quote: 'Good quality cotton, slightly loose in waist.', user: 'wearitout', product: 'Classic Oxford Shirt' },
]

const HERO_IMAGES = [
  { src: '/images/products/shirt-worn.jpg', alt: 'Classic Oxford Shirt, worn', rotate: '-rotate-3', z: 'z-10' },
  { src: '/images/products/dress-worn.jpg', alt: 'Floral Wrap Dress, worn', rotate: 'rotate-2', z: 'z-20' },
  { src: '/images/products/jeans-worn.jpg', alt: 'Slim Tapered Jeans, worn', rotate: '-rotate-1', z: 'z-30' },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-page-gradient">
      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-16 pb-16">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10 items-center">
          <div className="md:col-span-7 stagger-child" style={{ '--stagger-i': 0 }}>
            <div className="font-accent italic text-sm tracking-[0.15em] text-accent uppercase mb-5">
              Sizing Intelligence Layer
            </div>
            <h1 className="font-display font-extrabold text-ink leading-[0.92] mb-7 text-[clamp(3rem,7.5vw,6rem)]">
              Clothes that fit,
              <br />
              <span className="text-outline">bought</span>{' '}
              <span className="font-accent italic font-medium text-accent">blind.</span>
            </h1>
            <p className="font-accent text-muted text-lg max-w-md leading-relaxed mb-8">
              fitOS turns thousands of buyer reviews and real size charts
              into one explainable size recommendation — before you order,
              not after the return.
            </p>
            <div className="flex flex-wrap items-center gap-4">
              <Link
                to="/shop"
                className="group inline-flex items-center gap-2 bg-ink text-white px-7 py-3.5 rounded-full font-medium hover:bg-accent transition-colors duration-300"
              >
                Browse the shop
                <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
              </Link>
              <a
                href="#how-it-works"
                className="link-underline text-ink font-medium text-sm"
              >
                How it works
              </a>
            </div>
          </div>

          {/* Photo stack */}
          <div className="md:col-span-5 stagger-child" style={{ '--stagger-i': 2 }}>
            <div className="relative flex justify-center items-center py-6">
              {HERO_IMAGES.map((img, i) => (
                <div
                  key={img.src}
                  className={`relative ${img.rotate} ${img.z} ${i > 0 ? '-ml-16 md:-ml-20' : ''} w-36 md:w-44 aspect-[3/4] rounded-xl overflow-hidden bg-[#EEEEE9] shadow-[var(--shadow-lifted)] border-4 border-surface hover:-translate-y-2 transition-transform duration-300`}
                >
                  <img src={img.src} alt={img.alt} className="w-full h-full object-cover" />
                </div>
              ))}
              <span className="absolute -bottom-1 right-0 md:right-4 bg-surface border border-ink/10 shadow-[var(--shadow-soft)] rounded-full px-3.5 py-1.5 text-xs font-medium text-accent flex items-center gap-1.5 z-40">
                <ShieldCheck size={13} /> Every piece fit-checked
              </span>
            </div>
          </div>
        </div>
      </section>

      <Marquee />

      {/* How it works */}
      <section id="how-it-works" className="max-w-6xl mx-auto px-6 py-20 scroll-mt-20">
        <div className="mb-12">
          <div className="font-accent italic text-sm tracking-[0.15em] text-accent uppercase mb-3">
            How it works
          </div>
          <h2 className="font-display font-extrabold text-ink text-4xl md:text-5xl leading-tight">
            Three steps to{' '}
            <span className="font-accent italic font-medium text-accent">your</span> size.
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {STEPS.map((step, i) => (
            <div
              key={step.title}
              className="stagger-child relative bg-surface rounded-2xl p-7 shadow-[var(--shadow-soft)] hover:shadow-[var(--shadow-lifted)] hover:-translate-y-1 transition-all duration-300"
              style={{ '--stagger-i': i }}
            >
              <span className="absolute top-6 right-6 font-display font-bold text-2xl text-ink/15">
                {String(i + 1).padStart(2, '0')}
              </span>
              <div className="w-11 h-11 rounded-full bg-accent/10 text-accent flex items-center justify-center mb-5">
                <step.icon size={20} />
              </div>
              <h3 className="font-display font-bold text-xl text-ink mb-2">{step.title}</h3>
              <p className="text-sm text-muted leading-relaxed">{step.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Fit Passport showcase */}
      <section className="border-y border-ink/10 bg-surface/60">
        <div className="max-w-6xl mx-auto px-6 py-20 grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="font-accent italic text-sm tracking-[0.15em] text-accent uppercase mb-3">
              Fit Passport
            </div>
            <h2 className="font-display font-extrabold text-ink text-4xl md:text-5xl leading-tight mb-6">
              Measured once.
              <br />
              <span className="text-outline">Honest everywhere.</span>
            </h2>
            <ul className="space-y-4 text-sm text-muted max-w-md">
              <li className="flex gap-3">
                <BadgeCheck size={18} className="text-accent shrink-0 mt-0.5" />
                <span>
                  <span className="font-medium text-ink">A fit score, not a sales pitch.</span>{' '}
                  Every recommendation comes with a 0-100 confidence score you can trust.
                </span>
              </li>
              <li className="flex gap-3">
                <Ruler size={18} className="text-accent shrink-0 mt-0.5" />
                <span>
                  <span className="font-medium text-ink">Tight to loose, per dimension.</span>{' '}
                  See exactly how the chest, waist, and hips will sit — in centimeters of ease.
                </span>
              </li>
              <li className="flex gap-3">
                <MessagesSquare size={18} className="text-accent shrink-0 mt-0.5" />
                <span>
                  <span className="font-medium text-ink">Caveats included.</span>{' '}
                  If 30% of reviewers said it runs small, we tell you — and show you their reviews.
                </span>
              </li>
            </ul>
          </div>

          {/* Static passport mock */}
          <div className="relative border border-accent/25 bg-gradient-to-br from-accent/8 to-accent/3 rounded-2xl shadow-[var(--shadow-lifted)] overflow-hidden max-w-md md:justify-self-end w-full">
            <div className="absolute top-0 left-0 h-full w-1 bg-accent/60" />
            <div className="p-6 pb-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2 text-accent text-sm font-medium">
                  <ShieldCheck size={16} /> Sizing Intelligence
                </div>
                <span className="font-accent italic text-[10px] tracking-[0.15em] text-accent/70 uppercase">
                  Fit Passport
                </span>
              </div>
              <div className="flex items-end gap-3 mb-5">
                <span className="font-display font-bold text-5xl text-ink leading-none">M</span>
                <span className="text-sm text-muted pb-0.5">
                  recommended · fit score <span className="font-semibold text-ink">86</span>/100
                </span>
              </div>
              <div className="space-y-3">
                <MockFitBar label="Chest" verdict="Ideal" position={55} tone="bg-accent" />
                <MockFitBar label="Waist" verdict="Ideal" position={48} tone="bg-accent" />
                <MockFitBar label="Hips" verdict="Loose" position={78} tone="bg-ink/40" />
              </div>
            </div>
            <div className="ticket-divider mx-6" />
            <div className="p-6 pt-4 text-xs text-muted font-accent italic">
              "Runs slightly small in the shoulders" — flagged from 12 reviews
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <div className="mb-12 flex flex-wrap items-end justify-between gap-4">
          <h2 className="font-display font-extrabold text-ink text-4xl md:text-5xl leading-tight">
            Real buyers,{' '}
            <span className="font-accent italic font-medium text-accent">real fits.</span>
          </h2>
          <span className="font-accent italic text-sm text-muted">
            Pulled straight from product reviews
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {TESTIMONIALS.map((t, i) => (
            <figure
              key={t.user}
              className="stagger-child bg-surface rounded-2xl p-7 shadow-[var(--shadow-soft)]"
              style={{ '--stagger-i': i }}
            >
              <div className="flex gap-0.5 mb-4">
                {Array.from({ length: 5 }).map((_, s) => (
                  <Star key={s} size={13} className="fill-accent text-accent" />
                ))}
              </div>
              <blockquote className="font-accent italic text-lg text-ink leading-relaxed mb-5">
                "{t.quote}"
              </blockquote>
              <figcaption className="flex items-center gap-2.5">
                <span className="w-8 h-8 rounded-full bg-accent/15 text-accent text-xs font-bold flex items-center justify-center uppercase">
                  {t.user.slice(0, 2)}
                </span>
                <span>
                  <span className="block text-sm font-medium text-ink">{t.user}</span>
                  <span className="block text-xs text-muted">{t.product}</span>
                </span>
              </figcaption>
            </figure>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section className="max-w-6xl mx-auto px-6 py-24 text-center">
        <h2 className="font-display font-extrabold text-ink leading-[0.95] text-[clamp(2.5rem,6vw,4.5rem)] mb-6">
          Never guess <span className="text-outline">your size</span>{' '}
          <span className="font-accent italic font-medium text-accent">again.</span>
        </h2>
        <p className="font-accent text-muted text-lg max-w-md mx-auto leading-relaxed mb-8">
          Four measurements. One honest answer. Zero guesswork.
        </p>
        <Link
          to="/shop"
          className="group inline-flex items-center gap-2 bg-ink text-white px-8 py-4 rounded-full font-medium hover:bg-accent transition-colors duration-300"
        >
          Start shopping
          <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
        </Link>
      </section>
    </div>
  )
}

function MockFitBar({ label, verdict, position, tone }) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-ink">{label}</span>
        <span className="text-muted">{verdict}</span>
      </div>
      <div className="relative h-1.5 bg-ink/10 rounded-full">
        <div
          className={`absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full ${tone}`}
          style={{ left: `calc(${position}% - 5px)` }}
        />
      </div>
    </div>
  )
}
