import os
from azure.devops.connection import Connection
from msrest.authentication import OAuthTokenAuthentication, BasicTokenAuthentication
from dotenv import load_dotenv

load_dotenv()

class ADOClient:
    def __init__(self):
        self.token = os.getenv("PAT")
        self.org_url = f"https://dev.azure.com/{os.getenv('ORG')}"
        self.project = os.getenv("PROJECT")

        token_dict = {'access_token': self.token}

        if not self.token or not self.org_url or not self.project:
            raise ValueError("Missing environment variables. Check your .env file!")

        credentials = BasicTokenAuthentication(token_dict)
        self.connection = Connection(base_url=self.org_url, creds=credentials)
        self.build_client = self.connection.clients.get_build_client()

    # test connection function to verify that we can connect to Azure DevOps and fetch some data
    # def test_connection(self):
    #     try:
    #         # We fetch a very small number of builds to just verify connectivity
    #         builds = self.build_client.get_builds(project=self.project, top=1)
    #         print("✅ Success! Connected to Azure DevOps.")
    #         print(f"Latest Build ID: {builds[0].id}")
    #     except Exception as e:
    #         print("❌ Connection Failed.")
    #         print(f"Error Details: {e}")

    def get_recent_builds(self):
        try:
            builds=self.build_client.get_builds(project=self.project, top=5)
            for build in builds:
                print(f"Build ID: {build.id}, Status: {build.status}, Result: {build.result}")
        except Exception as e:
            print("❌ Failed to fetch builds.")
            print(f"Error Details: {e}")


    # to fetch the pipeline logs for a specific build, we need to first get the list of log references for that build, and then fetch the content of those logs. The logs are typically stored in chunks, so we need to iterate through them and decode the byte streams into readable text.        
    
    def get_build_logs(self, build_id, all_logs=True):
        """
        Fetches and prints the text content of the build logs.

        By default this will iterate and print all log files associated with the build.
        Set `all_logs=False` to fetch only the first log reference.

        Returns the combined log text (string) or an error message.
        """
        try:
            # 1. Get the list of log references (metadata)
            log_refs = self.build_client.get_build_logs(project=self.project, build_id=build_id)

            if not log_refs:
                msg = "No logs found for this build."
                print(msg)
                return msg

            combined_text = ""

            # Iterate over each log reference and fetch its contents
            for idx, ref in enumerate(log_refs):
                # Fetch the content for this log ID
                log_stream = self.build_client.get_build_log(
                    project=self.project,
                    build_id=build_id,
                    log_id=ref.id,
                )

                # Convert the returned value into text robustly
                if isinstance(log_stream, (bytes, bytearray)):
                    text = log_stream.decode('utf-8', errors='replace')
                elif isinstance(log_stream, str):
                    text = log_stream
                else:
                    # Try iterating the stream
                    try:
                        parts = []
                        for chunk in log_stream:
                            if isinstance(chunk, (bytes, bytearray)):
                                parts.append(chunk.decode('utf-8', errors='replace'))
                            else:
                                parts.append(str(chunk))
                        text = "".join(parts)
                    except TypeError:
                        # Not iterable; fallback
                        text = str(log_stream)

                # Print a small header so it's easy to see which log file this came from
                header_name = getattr(ref, 'path', None) or getattr(ref, 'log', None) or f"log {ref.id}"
                header = f"\n--- Log {idx + 1}/{len(log_refs)}: {header_name} (id={ref.id}) ---\n"
               # print(header + text)
                #header_text = header + text
                combined_text += header + text

                if not all_logs:
                    break

            return combined_text

        except Exception as e:
            msg = f"Error fetching logs: {e}"
            print(msg)
            return msg
    


if __name__ == "__main__":
    ado_client = ADOClient()
    ado_client.get_recent_builds()
    print(ado_client.get_build_logs(68))  # Example build ID to fetch logs for



