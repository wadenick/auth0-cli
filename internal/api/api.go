package api

import (
	"context"
	"time"

	"github.com/cyx/auth0/management"
)

// We wait up to 1minute for a full deploy operation to complete.  Typically
// this takes 1-5s (no deps), or 10-20s (LOTS of npm deps).
const deployMaxTimeout = time.Minute

func New(mgmt *management.Management) *API {
	return &API{Management: mgmt}
}

// API is the command surface are for use in auth0-cli. The intent is to expose
// the domain language.
type API struct {
	*management.Management
}

func (a *API) DeployAction(ctx context.Context, actionID string, v *management.ActionVersion) (<-chan *management.ActionVersion, <-chan error) {
	errCh := make(chan error, 1)
	versionCh := make(chan *management.ActionVersion)

	if err := a.Management.ActionVersion.Create(actionID, v); err != nil {
		errCh <- err

		close(errCh)
		close(versionCh)
		return versionCh, errCh
	}

	go func() {
		defer close(versionCh)
		defer close(errCh)

		var status management.VersionStatus

		// Wait up to 1 minute for deploying an action version.
		ctx, cancel := context.WithTimeout(context.Background(), deployMaxTimeout)
		defer cancel()

		ticker := time.NewTicker(time.Second)
		defer ticker.Stop()

		for {
			select {
			case <-ctx.Done():
				errCh <- ctx.Err()
				return

			case <-ticker.C:
				got, err := a.Management.ActionVersion.Read(actionID, v.ID)
				if err != nil {
					errCh <- err
					return
				}

				if status != got.Status {
					versionCh <- got
				}

				if got.Status == management.VersionStatusBuilt {
					return
				}
			}
		}
	}()

	return versionCh, errCh
}
