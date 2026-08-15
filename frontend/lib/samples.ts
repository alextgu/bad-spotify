import type { Session } from '@/lib/types';
import libraryBirthdayGymSession from '@/public/sessions/library-birthday-gym.json';
import officeFoodCourtSession from '@/public/sessions/office-food-court.json';
import winterForestWalkSession from '@/public/sessions/winter-forest-walk.json';

/** One real clip and the footage-derived session shown beside it. */
export interface Sample {
  id: string;
  title: string;
  blurb: string;
  length: string;
  durationS: number;
  src: string;
  session: Session;
  placeholder?: boolean;
}

/** Three real clips, each paired with its own generated analysis session. */
export const samples: Sample[] = [
  {
    id: 'library-birthday-gym',
    title: 'Library → Birthday → Gym',
    blurb:
      'Gemini catches all three transitions: focused library, joyful birthday, then determined gym — answered with nu metal and dramatic classical.',
    length: '00:53',
    durationS: 52.75,
    src: '/videos/library-birthday-gym.mp4',
    session: libraryBirthdayGymSession as unknown as Session,
  },
  {
    id: 'office-food-court',
    title: 'Office → Food Court',
    blurb:
      'A focused open-plan office becomes a bustling mall food court. Gemini answers with Bodies, then gentle Satie.',
    length: '00:32',
    durationS: 32,
    src: '/videos/office-food-court.mp4',
    session: officeFoodCourtSession as unknown as Session,
  },
  {
    id: 'winter-forest-walk',
    title: 'Winter Forest Walk',
    blurb:
      'A tranquil walk along a snow-covered pine trail, confidently answered with Barbie Girl.',
    length: '00:20',
    durationS: 20.49,
    src: '/videos/winter-forest-walk.mp4',
    session: winterForestWalkSession as unknown as Session,
  },
];
