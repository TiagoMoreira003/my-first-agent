import datasets
from langchain_core.documents import Document

# Load the dataset
club_dataset = datasets.load_dataset("text", data_files={"train": "./portuguese-clubs.txt"}, 
                                      sample_by="line")

docs = [Document(page_content=line["text"],
                metadata={"source": "./portuguese-clubs.txt"}) for line in club_dataset["train"]]