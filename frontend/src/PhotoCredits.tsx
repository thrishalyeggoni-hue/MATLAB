import { PORTRAITS } from "./portraitAssets";
import { AngularPanel } from "./components";
export default function PhotoCredits() {
  return (
    <AngularPanel className="photo-credits" id="photo-credits">
      <span className="eyebrow">THE PEOPLE BEHIND THE PICTURES</span>
      <h2>Driver photography.</h2>
      <p>
        Real photographs from Wikimedia Commons. Portraits identify the driver
        and may come from a different year than the selected session; team names
        and colours always come from the recorded session. Original image files
        are retained. The card view crops and fades their edges using CSS,
        without retouching faces.
      </p>
      <p>
        Each photograph retains the licence linked below, including share-alike
        terms where applicable. Source pages identify existing crops and
        contributors. No photographer, driver, team, or licensor endorses this
        project.
      </p>
      <div className="photo-credit-grid">
        {PORTRAITS.map((photo) => (
          <div key={photo.src}>
            <strong>
              {photo.name} <small>{photo.photoYear}</small>
            </strong>
            <span>{photo.author}</span>
            <div>
              <a href={photo.source} target="_blank" rel="noreferrer">
                Photo & source ↗
              </a>
              <a href={photo.licenseUrl} target="_blank" rel="noreferrer">
                {photo.license} ↗
              </a>
            </div>
          </div>
        ))}
      </div>
      <a
        className="credits-download"
        href="/portraits/credits.json"
        target="_blank"
        rel="noreferrer"
      >
        Full image attribution manifest ↗
      </a>
    </AngularPanel>
  );
}
