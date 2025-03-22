import { Connection } from "mongoose"


type FeatureCard={
    title: string;
    icon:  ForwardRefExoticComponent<Omit<LucideProps, "ref"> & RefAttributes<SVGSVGElement>>;
    highlights: Array<string>;
    details:string;
    href:string|null;
    requirements:string|null;
}

export {FeatureCard}