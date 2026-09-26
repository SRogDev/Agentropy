import {
  Comparison,
  Faq,
  FeaturesGrid,
  FinalCta,
  Hero,
  HowItWorks,
  LandingFooter,
  LandingNav,
  PricingPreview,
  Problem,
} from "@/features/landing/sections";

export default function LandingPage() {
  return (
    <>
      <LandingNav />
      <main>
        <Hero />
        <Problem />
        <HowItWorks />
        <FeaturesGrid />
        <Comparison />
        <PricingPreview />
        <Faq />
        <FinalCta />
      </main>
      <LandingFooter />
    </>
  );
}
